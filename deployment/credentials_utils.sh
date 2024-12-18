# repo_path is declared in other scripts that source this one
credentials_path="$repo_path/deployment/default_credentials.txt"

### 
# Default password generation and reuse for upgrade

generate_random_password() {
  local CHAR_SET="a-zA-Z0-9"
  local LENGTH=12
  random_string=$(tr -dc "$CHAR_SET" < /dev/urandom | head -c $LENGTH)
  echo "$random_string"
}

load_credentials() {
  # will load into local environment variables values from default_credentials.txt file in a form of target_USERNAME and target_PASSWORD
  source $credentials_path
}

store_credentials() {
  # store give "username" and "password" as $target_USERNAME and $target_PASSWORD variables in default_credentials.txt file
  local target username password
  target=$1
  username=$2
  password=$3
  # remove old entry (if file exists)
  if [ -f "$credentials_path" ]; then
    sed -i "/^${target}_USERNAME=/d" $credentials_path
    sed -i "/^${target}_PASSWORD=/d" $credentials_path
  fi
  # always store new password
  echo "${target}_USERNAME=${username} " >> $credentials_path
  echo "${target}_PASSWORD=${password}" >> $credentials_path
}

get_or_create_and_store_credentials() {
  # Parameters:
  # target - e.g. GRAFANA or KEYCLOAK_ERAG_ADMIN or KEYCLOAK_REALM_ADMIN or KEYCLOAK_ERAG_USER
  # username/password to store in default_credentials.txt
  # Returns variables:
  # use NEW_PASSWORD and NEW_USERNAME afterwards to get latest password
  local target username password password_varname
  target=$1
  username=$2
  password=$3

  if [ "$password" == "" ] ; then                                   # if not provided by command line or environment variables to script
    if [ -f $credentials_path ] ; then
        echo "Loading $target default credentials from file: $credentials_path"
        load_credentials
        password_varname=${target}_PASSWORD
        password="${!password_varname}"
    fi
    if [ "$password" == "" ] ; then # if password wasn't provided by cmdline nor environment nor found in file
        echo "Generating random credentials for $target and storing in $credentials_path"
        password=$(generate_random_password)
    fi
  else
    echo "Using provided credentials for $target"
  fi
  # always store new password provided by command line or restored from file or generated
  store_credentials $target $username $password

  NEW_PASSWORD=$password
  NEW_USERNAME=$username
}
