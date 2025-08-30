# Build phase
FROM node:20 as build

WORKDIR /app

# Copy package files trước để tận dụng Docker layer caching
COPY package*.json ./

# Cài đặt dependencies với --legacy-peer-deps nếu cần
RUN npm install --silent --legacy-peer-deps

# Verify react-scripts đã được cài đặt
RUN ls -la node_modules/.bin/ | grep react-scripts || echo "react-scripts not found"

# Copy toàn bộ source code
COPY . .

# Build app
RUN npm run build

# Serve phase
FROM nginx:stable-alpine

# Copy build vào NGINX
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx config nếu có
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]