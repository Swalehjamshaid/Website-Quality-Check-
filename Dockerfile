FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production --legacy-peer-deps  # Or npm install

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build  # If you have this script

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app ./
EXPOSE $PORT
CMD ["npm", "start"]
