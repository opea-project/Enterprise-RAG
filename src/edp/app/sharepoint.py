# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import asyncio
import os
import time
from contextlib import contextmanager
from urllib.parse import quote, urlparse, urlunparse

import httpx
from redis import Redis

from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger("edp_microservice")

# Per-event-loop async HTTP client.
# A new client is created whenever the running event loop changes (e.g. each
# Celery task invocation calls asyncio.run(), which creates and closes its own
# loop). Reusing a client across loops causes "event loop is closed" errors
# because httpx's internal asyncio primitives are bound to the original loop.
_http_client: httpx.AsyncClient | None = None
_http_client_loop: object | None = None


async def _get_http_client() -> httpx.AsyncClient:
    global _http_client, _http_client_loop
    loop = asyncio.get_running_loop()
    if _http_client is None or _http_client_loop is not loop:
        _http_client = httpx.AsyncClient()
        _http_client_loop = loop
    return _http_client


# ---------------------------------------------------------------------------
# Environment / constants
# ---------------------------------------------------------------------------

SHAREPOINT_TENANT_ID = os.getenv('SHAREPOINT_TENANT_ID', '')
SHAREPOINT_CLIENT_ID = os.getenv('SHAREPOINT_CLIENT_ID', '')
SHAREPOINT_CLIENT_SECRET = os.getenv('SHAREPOINT_CLIENT_SECRET', '')
GRAPH_API_BASE = 'https://graph.microsoft.com/v1.0'

# Prefixes / names to skip (hidden dirs, temp upload chunks, SP system dirs)
SP_SKIP_PREFIXES = ('.', '~$', '_vti_')
SP_SKIP_NAMES = frozenset({'Forms', 'Preservation Hold Library'})
SP_SKIP_SEGMENTS = frozenset({'.uploads'})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class GraphApiError(Exception):
    """Raised when Microsoft Graph API returns a non-200 response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


# ---------------------------------------------------------------------------
# Small pure helpers
# ---------------------------------------------------------------------------

def sharepoint_enabled() -> bool:
    """Return True when all three SharePoint env vars are set."""
    return all([SHAREPOINT_TENANT_ID, SHAREPOINT_CLIENT_ID, SHAREPOINT_CLIENT_SECRET])


def site_display_name(record) -> str:
    """Return the preferred display name for a SharePointSiteRecord."""
    return record.display_name or record.name or record.graph_site_id


# ---------------------------------------------------------------------------
# Distributed sync lock (Redis-based)
# ---------------------------------------------------------------------------

_SP_SYNC_LOCK_KEY = 'edp:sharepoint:sync_lock'
_SP_SYNC_LOCK_TTL = int(os.getenv('EDP_SP_SYNC_LOCK_TTL_SECONDS', '600'))


def _get_redis() -> Redis:
    return Redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))


@contextmanager
def sp_sync_lock(blocking: bool = True):
    """Acquire a distributed lock for SharePoint sync.

    Args:
        blocking: If True, raises ``SpSyncLockError`` when the lock cannot
                  be acquired.  If False, yields ``False`` instead so the
                  caller can silently skip.
    Yields:
        ``True`` when the lock was acquired, ``False`` when *blocking* is
        ``False`` and the lock was already held.
    """
    r = _get_redis()
    acquired = r.set(_SP_SYNC_LOCK_KEY, 'locked', nx=True, ex=_SP_SYNC_LOCK_TTL)
    if not acquired:
        if blocking:
            raise SpSyncLockError()
        yield False
        return
    try:
        yield True
    finally:
        r.delete(_SP_SYNC_LOCK_KEY)


class SpSyncLockError(Exception):
    """Raised when the SharePoint sync lock cannot be acquired."""


# ---------------------------------------------------------------------------
# Microsoft Graph authentication
# ---------------------------------------------------------------------------

# Module-level token cache to avoid re-authenticating on every request.
_graph_token_cache: dict = {}  # {"access_token": str, "expires_at": float}


async def _get_graph_client_token() -> str:
    """Acquire an application-level client-credentials token for Microsoft Graph.

    Caches the token in-process and refreshes 60 s before expiry.
    """
    if not sharepoint_enabled():
        raise ValueError(
            "SharePoint integration is not configured. "
            "Set SHAREPOINT_TENANT_ID, SHAREPOINT_CLIENT_ID and "
            "SHAREPOINT_CLIENT_SECRET environment variables."
        )

    now = time.time()
    if _graph_token_cache.get('access_token') and _graph_token_cache.get('expires_at', 0) > now + 60:
        return _graph_token_cache['access_token']

    token_url = f"https://login.microsoftonline.com/{SHAREPOINT_TENANT_ID}/oauth2/v2.0/token"
    resp = await (await _get_http_client()).post(
        token_url,
        data={
            'grant_type': 'client_credentials',
            'client_id': SHAREPOINT_CLIENT_ID,
            'client_secret': SHAREPOINT_CLIENT_SECRET,
            'scope': 'https://graph.microsoft.com/.default',
        },
        timeout=15,
    )

    if resp.status_code != 200:
        logger.error(f"Microsoft token request failed ({resp.status_code}): {resp.text}")
        raise ValueError(
            f"Could not acquire Microsoft Graph token (HTTP {resp.status_code}). "
            "Check SHAREPOINT_TENANT_ID / CLIENT_ID / CLIENT_SECRET."
        )

    data = resp.json()
    access_token = data.get('access_token')
    if not access_token:
        raise ValueError("Microsoft token response did not contain an access_token.")

    _graph_token_cache['access_token'] = access_token
    _graph_token_cache['expires_at'] = now + data.get('expires_in', 3600)

    logger.debug("Acquired new Microsoft Graph client-credentials token.")
    return access_token


async def get_graph_token() -> str:
    """Public wrapper — returns a valid Microsoft Graph access token."""
    return await _get_graph_client_token()


async def get_user_ms_token(keycloak_access_token: str) -> str:
    """Exchange a Keycloak access token for the stored Microsoft identity-provider token.

    Keycloak must be configured with ``storeToken: true`` on the IDP.

    Returns the user's Microsoft Graph access token stored by Keycloak.
    """
    oidc_config_url = os.getenv('EDP_OIDC_CONFIG_URL', '')
    idp_alias = os.getenv('KEYCLOAK_BROKER_IDP_ALIAS', '')
    logger.info(f"Exchanging Keycloak token for Microsoft Graph token via broker at {oidc_config_url} with IDP alias '{idp_alias}'")
    if not oidc_config_url or not idp_alias:
        raise ValueError(
            "Keycloak broker token exchange not configured. "
            "Set EDP_OIDC_CONFIG_URL and KEYCLOAK_BROKER_IDP_ALIAS."
        )

    base_url = oidc_config_url.rsplit('/.well-known/', 1)[0]
    broker_url = f"{base_url}/broker/{idp_alias}/token"

    resp = await (await _get_http_client()).get(
        broker_url,
        headers={"Authorization": f"Bearer {keycloak_access_token}"},
        timeout=15,
    )

    if resp.status_code != 200:
        raise ValueError(
            f"Keycloak broker token request failed (HTTP {resp.status_code}): {resp.text}"
        )

    token_data = resp.text
    for part in token_data.split('&'):
        if part.startswith('access_token='):
            return part.split('=', 1)[1]

    try:
        data = resp.json()
        if 'access_token' in data:
            return data['access_token']
    except Exception:
        pass

    raise ValueError("Could not extract access_token from Keycloak broker response.")


# ---------------------------------------------------------------------------
# Microsoft Graph API helpers
# ---------------------------------------------------------------------------

async def graph_api_get(ms_access_token: str, path: str, params: dict = None) -> dict:
    """Perform an authenticated GET request against Microsoft Graph API."""
    url = f"{GRAPH_API_BASE}{path}"
    resp = await (await _get_http_client()).get(
        url,
        headers={"Authorization": f"Bearer {ms_access_token}"},
        params=params,
        timeout=30,
    )

    if resp.status_code != 200:
        logger.error(f"Graph API error ({resp.status_code}) for {path}: {resp.text}")
        error_output = resp.json()
        raise GraphApiError(
            status_code=resp.status_code,
            detail=f"Microsoft Graph API error for site: {path}, status: {resp.status_code}, response: {error_output['error']['message']}",
        )

    return resp.json()


async def _graph_api_get_url(ms_access_token: str, url: str) -> dict:
    """GET a full Graph API URL (used for @odata.nextLink pagination)."""
    resp = await (await _get_http_client()).get(
        url,
        headers={"Authorization": f"Bearer {ms_access_token}"},
        timeout=30,
    )

    if resp.status_code != 200:
        logger.error(f"Graph API pagination error ({resp.status_code}): {resp.text}")
        error_output = resp.json()
        raise GraphApiError(
            status_code=resp.status_code,
            detail=f"Microsoft Graph API error - status: {resp.status_code}, response: {error_output['error']['message']}",
        )

    return resp.json()


async def user_can_access_site(ms_user_token: str, site_id: str) -> bool:
    """Check whether the user's delegated MS token can access a SP site."""
    try:
        await graph_api_get(ms_user_token, f'/sites/{site_id}/drive')
        return True
    except GraphApiError as e:
        if e.status_code in (401, 403):
            return False
        logger.warning(f"Unexpected Graph error checking site {site_id} access: {e}")
        return False
    except Exception as e:
        logger.warning(f"Error checking site {site_id} access: {e}")
        return False


def clean_sharepoint_site_url(site_url: str) -> str:
    """Return the canonical site URL, stripping library paths and query strings.
    """
    parsed = urlparse(site_url)
    parts = [p for p in parsed.path.split('/') if p]
    if not parts:
        clean_path = ''  # root site
    elif len(parts) >= 2 and parts[0] in ('sites', 'teams'):
        clean_path = f'/{parts[0]}/{parts[1]}'
    else:
        raise ValueError(
            f"URL does not point to a SharePoint site or Teams channel: {site_url!r}. "
            "Expected format: https://<tenant>.sharepoint.com/sites/<site-name>"
        )
    return urlunparse((parsed.scheme, parsed.netloc, clean_path, '', '', ''))


async def resolve_single_sharepoint_site(ms_access_token: str, site_url: str) -> dict:
    """Resolve a single SharePoint site URL to its Graph site object."""
    parsed = urlparse(site_url)
    hostname = parsed.hostname
    rel_path = parsed.path.rstrip('/')
    if not hostname:
        raise ValueError(f"Cannot parse hostname from URL: {site_url}")

    if rel_path and rel_path != '/':
        graph_path = f'/sites/{hostname}:{rel_path}'
    else:
        graph_path = f'/sites/{hostname}'

    return await graph_api_get(ms_access_token, graph_path)


# ---------------------------------------------------------------------------
# SharePoint file listing / download / upload / delete
# ---------------------------------------------------------------------------

async def _list_drive_items_recursive(
    ms_access_token: str,
    drive_id: str,
    folder_id: str = None,
    path_prefix: str = "",
) -> list:
    """Recursively list all file items in a SharePoint drive/folder."""
    if folder_id:
        api_path = f'/drives/{drive_id}/items/{folder_id}/children'
    else:
        api_path = f'/drives/{drive_id}/root/children'

    data = await graph_api_get(ms_access_token, api_path)
    files = []

    def _should_skip(name: str, full_path: str) -> bool:
        if any(name.startswith(p) for p in SP_SKIP_PREFIXES):
            return True
        if name in SP_SKIP_NAMES:
            return True
        if any(seg in SP_SKIP_SEGMENTS for seg in full_path.split('/')):
            return True
        return False

    async def _process_items(items):
        for item in items:
            item_name = item.get('name', '')
            item_path = f"{path_prefix}{item_name}"

            if _should_skip(item_name, item_path):
                continue

            if 'folder' in item:
                sub_files = await _list_drive_items_recursive(
                    ms_access_token, drive_id, item['id'], f"{item_path}/",
                )
                files.extend(sub_files)
            else:
                files.append({
                    'item_id': item['id'],
                    'name': item_name,
                    'path': item_path,
                    'size': item.get('size', 0),
                    'etag': item.get('eTag', ''),
                    'content_type': item.get('file', {}).get('mimeType', 'application/octet-stream'),
                    'last_modified': item.get('lastModifiedDateTime', ''),
                    'drive_id': drive_id,
                })

    await _process_items(data.get('value', []))

    next_link = data.get('@odata.nextLink')
    while next_link:
        page_data = await _graph_api_get_url(ms_access_token, next_link)
        await _process_items(page_data.get('value', []))
        next_link = page_data.get('@odata.nextLink')

    return files


async def list_sharepoint_site_files(ms_access_token: str, graph_site_id: str) -> list:
    """List all files across all drives in a SharePoint site, recursively."""
    drives_data = await graph_api_get(ms_access_token, f'/sites/{graph_site_id}/drives')
    all_files = []

    for drive in drives_data.get('value', []):
        drive_id = drive['id']
        drive_name = drive.get('name', drive_id)
        drive_files = await _list_drive_items_recursive(ms_access_token, drive_id)
        for f in drive_files:
            f['drive_name'] = drive_name
        all_files.extend(drive_files)

    return all_files


async def upload_sharepoint_file(
    ms_access_token: str,
    site_id: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str = "application/octet-stream",
) -> dict:
    """Upload a file to the root of the default document library."""
    url = (
        f"{GRAPH_API_BASE}/sites/{site_id}/drive/root:"
        f"/{quote(file_name, safe='')}:/content"
    )

    resp = await (await _get_http_client()).put(
        url,
        headers={
            "Authorization": f"Bearer {ms_access_token}",
            "Content-Type": content_type,
        },
        content=file_bytes,
        timeout=300,
    )

    if resp.status_code not in (200, 201):
        raise GraphApiError(
            status_code=resp.status_code,
            detail=f"Failed to upload file to SharePoint (HTTP {resp.status_code}): {resp.text}",
        )

    return resp.json()


# ---------------------------------------------------------------------------
# EDP-level SharePoint helpers
# ---------------------------------------------------------------------------


async def _resolve_drive_id(ms_token: str, graph_site_id: str, object_name: str) -> tuple[str, str]:
    """Parse *object_name* and resolve the target drive ID.

    ``object_name`` has the form ``{drive_name}/{relative_path}``.

    Returns:
        (target_drive_id, rel_path)
    """
    drive_name, _, rel_path = object_name.partition('/')
    if not rel_path:
        rel_path = drive_name
        drive_name = ''

    drives_data = await graph_api_get(ms_token, f'/sites/{graph_site_id}/drives')
    target_drive_id = None
    for d in drives_data.get('value', []):
        if d.get('name', '') == drive_name:
            target_drive_id = d['id']
            break

    if target_drive_id is None:
        drive_data = await graph_api_get(ms_token, f'/sites/{graph_site_id}/drive')
        target_drive_id = drive_data['id']

    return target_drive_id, rel_path


def get_tracked_sp_site_names():
    """Return display names for all tracked SharePoint sites.

    Used in ``list_bucket_with_permissions`` so the retriever can
    include SharePoint-sourced chunks in RBAC filtering.
    """
    from app.database import get_db
    from app.models import SharePointSiteRecord

    with get_db() as db:
        sites = db.query(SharePointSiteRecord).all()
        return [site_display_name(s) for s in sites]


async def filter_sp_sites_for_user(keycloak_token: str, sp_site_names: list) -> list:
    """Return only SP site names whose SharePoint sites the user can access."""
    if not sp_site_names:
        return []

    try:
        ms_user_token = await get_user_ms_token(keycloak_token)
    except Exception as e:
        logger.warning(f"Broker token exchange failed; cannot check SP access: {e}")
        return []

    from app.database import get_db
    from app.models import SharePointSiteRecord

    # Build map: display_name -> graph_site_id
    with get_db() as db:
        sites = db.query(SharePointSiteRecord).all()
        name_to_site_id = {site_display_name(s): s.graph_site_id for s in sites}

    accessible = []
    for sn in sp_site_names:
        site_id = name_to_site_id.get(sn)
        if not site_id:
            continue
        if await user_can_access_site(ms_user_token, site_id):
            accessible.append(sn)
            logger.info(f"User has access to SP site {site_id}")
        else:
            logger.debug(f"User denied access to SP site {site_id}")

    return accessible


async def download_sp_file_by_path(graph_site_id: str, object_name: str) -> bytes:
    """Download a file from SharePoint given the site ID and the object_name.

    ``object_name`` has the form ``{drive_name}/{relative_path}``.
    The function resolves the drive by name, then downloads via the
    ``/root:/{path}:/content`` Graph API endpoint.
    """
    ms_token = await get_graph_token()
    target_drive_id, rel_path = await _resolve_drive_id(ms_token, graph_site_id, object_name)

    encoded_path = quote(rel_path, safe='/')
    url = f"{GRAPH_API_BASE}/drives/{target_drive_id}/root:/{encoded_path}:/content"
    resp = await (await _get_http_client()).get(
        url,
        headers={"Authorization": f"Bearer {ms_token}"},
        timeout=120,
        follow_redirects=True,
    )

    if resp.status_code != 200:
        raise GraphApiError(
            status_code=resp.status_code,
            detail=f"Failed to download SharePoint file by path (HTTP {resp.status_code})",
        )

    return resp.content


async def delete_sp_file_by_path(graph_site_id: str, object_name: str) -> None:
    """Delete a file from SharePoint given the site ID and the object_name.

    ``object_name`` has the form ``{drive_name}/{relative_path}``.
    """
    ms_token = await get_graph_token()
    target_drive_id, rel_path = await _resolve_drive_id(ms_token, graph_site_id, object_name)

    encoded_path = quote(rel_path, safe='/')
    url = f"{GRAPH_API_BASE}/drives/{target_drive_id}/root:/{encoded_path}:"
    resp = await (await _get_http_client()).delete(
        url,
        headers={"Authorization": f"Bearer {ms_token}"},
        timeout=120,
    )

    if resp.status_code not in (200, 204):
        raise GraphApiError(
            status_code=resp.status_code,
            detail=f"Failed to delete SharePoint file (HTTP {resp.status_code}): {resp.text}",
        )

    logger.info(f"Deleted file '{object_name}' from SharePoint site {graph_site_id}.")


async def get_sharepoint_file_url(graph_site_id: str, object_name: str) -> str | None:
    """Return the SharePoint web URL for a file.

    ``object_name`` has the form ``{drive_name}/{relative_path}``.
    """
    ms_token = await get_graph_token()
    target_drive_id, rel_path = await _resolve_drive_id(ms_token, graph_site_id, object_name)

    try:
        encoded_path = quote(rel_path, safe='/')
        item = await graph_api_get(
            ms_token,
            f'/drives/{target_drive_id}/root:/{encoded_path}:',
            {'$select': 'webUrl'},
        )
        return item.get('webUrl')
    except GraphApiError as e:
        logger.warning(f"Could not resolve SP URL for {graph_site_id}/{object_name}: {e}")
        return None


# ---------------------------------------------------------------------------
# SharePoint sync plan (used by both GET and POST /api/sharepoint/sync)
# ---------------------------------------------------------------------------

async def build_sharepoint_sync_plan():
    """Compare files in tracked SharePoint sites with the database.

    Works like ``sync_files`` for S3 buckets: SharePoint is the source of
    truth and PostgreSQL ``FileStatus`` rows track the processing state.

    Returns:
        (actions, ms_token) where actions is a list of tuples:
        ('add'|'update'|'delete'|'no action', site_name, object_name,
         file_info_or_none, graph_site_id)
    """
    from app.database import get_db
    from app.models import FileStatus, SharePointSiteRecord

    ms_token = await get_graph_token()

    with get_db() as db:
        sites = db.query(SharePointSiteRecord).all()
        site_list = [
            (s.graph_site_id, site_display_name(s))
            for s in sites
        ]

    all_sp_files = {}
    sp_site_names = set()

    for graph_site_id, display_name in site_list:
        sp_site_names.add(display_name)
        try:
            files = await list_sharepoint_site_files(ms_token, graph_site_id)
            for f in files:
                object_name = f"{f['drive_name']}/{f['path']}"
                all_sp_files[(display_name, object_name)] = (f, graph_site_id)
        except Exception as e:
            logger.error(f"Error listing files for SharePoint site '{display_name}': {e}")

    actions = []

    with get_db() as db:
        # Check SP files against DB
        for (sn, object_name), (file_info, graph_site_id) in all_sp_files.items():
            file_status = db.query(FileStatus).filter(
                FileStatus.site_name == sn,
                FileStatus.object_name == object_name,
                FileStatus.marked_for_deletion == False,  # noqa: E712
            ).first()

            if file_status:
                if file_status.size != file_info['size']:
                    actions.append(('update', sn, object_name, file_info, graph_site_id))
                else:
                    actions.append(('no action', sn, object_name, None, graph_site_id))
            else:
                actions.append(('add', sn, object_name, file_info, graph_site_id))

        # Check for files in DB that no longer exist on SP
        for sn in sp_site_names:
            sp_files_in_db = db.query(FileStatus).filter(
                FileStatus.site_name == sn,
                FileStatus.marked_for_deletion == False,  # noqa: E712
            ).all()

            for f in sp_files_in_db:
                if (f.site_name, f.object_name) not in all_sp_files:
                    graph_site_id = next(
                        (sid for sid, dn in site_list if dn == sn),
                        '',
                    )
                    actions.append(('delete', f.site_name, f.object_name, None, graph_site_id))

    return actions, ms_token


def delete_sp_file(site_name, object_name):
    """Delete a SharePoint-sourced file from the database and vector store."""
    from app.main import delete_existing_file
    delete_existing_file(object_name, site_name=site_name)
