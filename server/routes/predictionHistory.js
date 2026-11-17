
import express from "express";
import { requireAuth } from "../middleware/auth.js";

import {
  savePrediction,
  getPredictionHistory,
  deletePrediction,
  clearPredictionHistory,
} from "../controllers/predictionHistoryController.js";

const router = express.Router();

// All routes require user authentication
router.use(requireAuth);

// Save a prediction
router.post("/", savePrediction);

// Get logged-in user's history
router.get("/", getPredictionHistory);

// Delete all history
router.delete("/", clearPredictionHistory);

// Delete one history record
router.delete("/:id", deletePrediction);

export default router;
