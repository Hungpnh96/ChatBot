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

# Build app với environment variables
ARG REACT_APP_API_URL
ARG REACT_APP_WS_URL
ARG NODE_ENV
RUN npm run build

# Serve phase - Sử dụng serve thay vì nginx
FROM node:20-alpine

# Cài đặt serve để serve static files
RUN npm install -g serve

# Copy build vào thư mục serve
COPY --from=build /app/build /app/build

WORKDIR /app

EXPOSE 80

# Serve React app
CMD ["serve", "-s", "build", "-l", "80"]