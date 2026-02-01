FROM node:18-alpine

WORKDIR /app

# Cache bust for Railway - forces rebuild
ARG CACHEBUST=1

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application
COPY . .

# Accept build arguments with default Railway backend URL
ARG NEXT_PUBLIC_API_URL=https://dependable-solace-production-75f7.up.railway.app
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Force cache bust and verify env var
RUN echo "Building with API_URL: $NEXT_PUBLIC_API_URL" && npm run build

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "start"]
