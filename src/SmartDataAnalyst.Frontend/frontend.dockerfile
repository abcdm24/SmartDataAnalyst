# frontend.dockerfile
# Multi-stage build: build with node, server with nginx

######### Stage 1: Build #########
FROM node:22-alpine AS build

WORKDIR /app

# Install build deps
# Use npm ci if you have package-loc.json, otherwise npm install
# Copy package files first for better cache.
COPY package.json bun.lock ./

# Install dependecies
RUN npm ci --silent || npm install --silent

# Copy source
COPY . .

# Build the app
RUN npm run build

######### Stage 2: Serve with nginx #########
FROM nginx:stable-alpine AS runtime

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder
COPY --from=build /app/dist /usr/share/nginx/html

# Add custom nginx config 
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Use the default nginx entrypoint
CMD ["nginx", "-g", "daemon off;"]


