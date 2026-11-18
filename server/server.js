
import "dotenv/config";
import express from "express";
import mongoose from "mongoose";
import cors from "cors";
import cookieParser from "cookie-parser";
import helmet from "helmet";
import rateLimit from "express-rate-limit";

import authRoutes from "./routes/auth.js";
import coffeeResearchRoutes from "./routes/coffeeResearch.js";
import predictionHistoryRoutes from "./routes/predictionHistory.js";

const app = express();
const PORT = Number(process.env.PORT) || 5000;

const CLIENT_ORIGIN =
  process.env.CLIENT_ORIGIN || "http://localhost:5173";

// Validate required environment variables
if (!process.env.MONGODB_URI) {
  throw new Error("MONGODB_URI is missing from server/.env");
}

if (!process.env.JWT_SECRET || process.env.JWT_SECRET.length < 32) {
  throw new Error(
    "JWT_SECRET must contain at least 32 characters in server/.env"
  );
}

// Security middleware
app.disable("x-powered-by");
app.use(helmet());

// CORS configuration
app.use(
  cors({
    origin: CLIENT_ORIGIN,
    credentials: true,
  })
);

// Request middleware
app.use(express.json({ limit: "10kb" }));
app.use(cookieParser());

// Health check
app.get("/api/health", (_req, res) => {
  res.json({
    success: true,
    message: "KisanVision AI authentication server is running.",
  });
});

// Authentication rate limiter
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  limit: 100,
  standardHeaders: "draft-8",
  legacyHeaders: false,
  message: {
    success: false,
    message: "Too many requests. Please try again later.",
  },
});

// API routes
app.use("/api/auth", authLimiter, authRoutes);
app.use("/api/research", coffeeResearchRoutes);
app.use("/api/history", predictionHistoryRoutes);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: "API endpoint not found.",
  });
});

// Global error handler
app.use((err, _req, res, _next) => {
  console.error("Server error:", err.message);

  if (err.type === "entity.parse.failed") {
    return res.status(400).json({
      success: false,
      message: "Invalid JSON request body.",
    });
  }

  if (err.name === "ValidationError") {
    return res.status(400).json({
      success: false,
      message: "Please check the submitted details.",
    });
  }

  return res.status(500).json({
    success: false,
    message: "An unexpected server error occurred.",
  });
});

// Start server and connect MongoDB
async function startServer() {
  try {
    await mongoose.connect(process.env.MONGODB_URI, {
      serverSelectionTimeoutMS: 10000,
    });

    console.log("Connected to MongoDB Atlas");

    app.listen(PORT, () => {
      console.log(
        `KisanVision AI authentication server running on port ${PORT}`
      );
    });
  } catch (error) {
    console.error("Startup failed:", error.message);
    process.exit(1);
  }
}

startServer();
