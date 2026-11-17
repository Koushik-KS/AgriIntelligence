
import mongoose from "mongoose";

const predictionHistorySchema = new mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "User",
      required: true,
      index: true,
    },

    crop: {
      type: String,
      required: true,
      enum: ["Coffee", "Arecanut", "Cardamom", "Ginger"],
    },

    disease: {
      type: String,
      required: true,
      trim: true,
    },

    confidence: {
      type: Number,
      required: true,
      min: 0,
      max: 100,
    },

    probabilities: [
      {
        name: {
          type: String,
          required: true,
        },
        value: {
          type: Number,
          required: true,
          min: 0,
          max: 100,
        },
        _id: false,
      },
    ],
  },
  {
    timestamps: true,
    versionKey: false,
  }
);

predictionHistorySchema.index({ userId: 1, createdAt: -1 });

const PredictionHistory = mongoose.model(
  "PredictionHistory",
  predictionHistorySchema
);

export default PredictionHistory;
