# repo_path is declared in other scripts that source this one
credentials_path="$repo_path/deployment/default_credentials.txt"

### 
# Default password generation and reuse for upgrade

generate_random_password() {
  local LENGTH=12
  local NUMERIC="0-9"
  local UPPERCASE="A-Z"
  local LOWERCASE="a-z"
  local SPECIAL="!_)"

  local password=$(tr -dc "$NUMERIC" < /dev/urandom | head -c 1)
  password+=$(tr -dc "$UPPERCASE" < /dev/urandom | head -c 1)
  password+=$(tr -dc "$LOWERCASE" < /dev/urandom | head -c 1)
  password+=$(tr -dc "$SPECIAL" < /dev/urandom | head -c 1)

  local ALL="$NUMERIC$UPPERCASE$LOWERCASE$SPECIAL"
  password+=$(tr -dc "$ALL" < /dev/urandom | head -c $(($LENGTH - 4)))

  password=$(echo "$password" | fold -w1 | shuf | tr -d '\n')
  echo "$password"
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

  if [ ! -f "$credentials_path" ]; then
    # create file with restricted access (owner: rw)
    touch $credentials_path
    chmod 600 $credentials_path
  else
    # remove old entry (if file exists)
    sed -i "/^${target}_USERNAME=/d" $credentials_path
    sed -i "/^${target}_PASSWORD=/d" $credentials_path
  fi

  # always store new password
  echo "${target}_USERNAME=${username} " >> $credentials_path
  echo "${target}_PASSWORD=\"${password}\"" >> $credentials_path
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

  if [ "$password" == "" ] ; then # if not provided by command line or environment variables to script
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

create_database_secret() {
    local DATABASE=$1
    local NAMESPACE_OF_SECRET=$2
    local DB_USERNAME=$3
    local DB_PASSWORD=$4
    local DB_NAMESPACE=$5
    local ADDITIONAL_ARG_1=$6

    if [[ "$DATABASE" == "redis" ]]; then
        kubectl get secret vector-database-config -n $NAMESPACE_OF_SECRET > /dev/null 2>&1 || kubectl create secret generic vector-database-config -n $NAMESPACE_OF_SECRET \
            --from-literal=VECTOR_STORE="$DATABASE" \
            --from-literal=REDIS_URL="redis://$DB_USERNAME:$VECTOR_DB_PASSWORD@redis-vector-db.$DB_NAMESPACE.svc" \
            --from-literal=REDIS_HOST="redis-vector-db.$DB_NAMESPACE.svc" \
            --from-literal=REDIS_PORT="6379" \
            --from-literal=REDIS_USERNAME="$DB_USERNAME" \
            --from-literal=REDIS_PASSWORD="$DB_PASSWORD" \
            --from-literal=VECTOR_DB_REDIS_ARGS="--save 60 1000 --appendonly yes --requirepass $DB_PASSWORD"
    elif [[ "$DATABASE" == "mongo" ]]; then
        kubectl get secret mongo-database-secret -n $NAMESPACE_OF_SECRET > /dev/null 2>&1 || kubectl create secret generic mongo-database-secret -n $NAMESPACE_OF_SECRET \
            --from-literal=MONGO_DATABASE_NAME="$ADDITIONAL_ARG_1" \
            --from-literal=MONGO_USER="$DB_USERNAME" \
            --from-literal=MONGO_PASSWORD="$DB_PASSWORD" \
            --from-literal=MONGO_HOST="fingerprint-mongodb.$DB_NAMESPACE.svc" \
            --from-literal=MONGO_PORT="27017"
    fi
}
