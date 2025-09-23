#!/bin/bash
# customize.sh script called with arguments: namespace KBS_ADDRESS
read -a args <<< $1
if [ "$args" -ne 2 ]; then
  echo "Error: Two arguments are required"
  exit 1
fi
cat - > "${KUSTOMIZE_HOME}/all.yaml"

# patch kustomization.yaml to use provided KBS_ADDRESS
cp "${KUSTOMIZE_HOME}/kustomization.yaml" "${KUSTOMIZE_HOME}/kustomization_org.yaml"
sed -i "s;KBS_ADDRESS;${args[1]};g" ${KUSTOMIZE_HOME}/kustomization.yaml

# Bypass for known limitation of kustomize
# https://github.com/kubernetes-sigs/kustomize/issues/5440 & https://github.com/kubernetes-sigs/kustomize/pull/5778 & https://github.com/kubernetes-sigs/kustomize/issues/5375
kustomize build "${KUSTOMIZE_HOME}" | yq eval '
                       . |= (
                         with(select(.kind == "StatefulSet" or .kind == "Deployment" or .kind == "DaemonSet");
                           with(select(.spec.template.spec.containers != null);
                             .spec.template.spec.containers |= map(.imagePullPolicy = "Always")
                           ) |
                           with(select(.spec.template.spec.initContainers != null);
                             .spec.template.spec.initContainers |= map(.imagePullPolicy = "Always")
                           )
                         )
                       )
                     '
# for debug purposes only
# -P - > "${KUSTOMIZE_HOME}/post.yaml"

# Recover kustomization.yaml
mv "${KUSTOMIZE_HOME}/kustomization_org.yaml" "${KUSTOMIZE_HOME}/kustomization.yaml"

# for debug purposes only
#cp "${KUSTOMIZE_HOME}/all.yaml" "${KUSTOMIZE_HOME}/${args[0]}"
rm "${KUSTOMIZE_HOME}/all.yaml"
