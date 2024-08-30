## This builds frontend Vite image. It runs in a init container where we should
## build the frontend. We can then copy the build to the nginx container for serving.
## As of now, building doesn't seem to work, so just running `npm run dev`.

FROM node:lts-slim as build-stage
WORKDIR /app
COPY package*.json ./
COPY ./ .
RUN npm install
#ENTRYPOINT sleep  40000
ENTRYPOINT npm run dev

# FROM nginx as production-stage
# RUN mkdir /app
# COPY --from=build-stage /app/dist /app
# COPY nginx.conf /etc/nginx/nginx.conf

# COPY ./replace_env_vars.sh /docker-entrypoint.d/replace_env_vars.sh
# RUN chmod +x /docker-entrypoint.d/replace_env_vars.sh