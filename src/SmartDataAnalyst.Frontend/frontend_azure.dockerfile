# Build stage
FROM oven/bun:latest AS build

WORKDIR /app

COPY . .
RUN bun install
ENV MODE_ENV=production
RUN bun run build --mode production

#Production stage (nginx)
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx","-g","daemon off;"]