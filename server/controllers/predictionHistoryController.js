
import PredictionHistory from "../models/PredictionHistory.js";

// Save a new prediction
export const savePrediction = async (req, res) => {
  try {
    const { crop, disease, confidence, probabilities } = req.body;

    if (!crop || !disease || confidence === undefined) {
      return res.status(400).json({
        success: false,
        message: "Crop, disease and confidence are required.",
      });
    }

    const record = await PredictionHistory.create({
      userId: req.userId,
      crop,
      disease,
      confidence,
      probabilities: Array.isArray(probabilities) ? probabilities : [],
    });

    return res.status(201).json({
      success: true,
      message: "Prediction saved successfully.",
      record,
    });
  } catch (error) {
    console.error("Save prediction error:", error);

    return res.status(500).json({
      success: false,
      message: "Unable to save prediction.",
    });
  }
};

// Get logged-in user's prediction history
export const getPredictionHistory = async (req, res) => {
  try {
    const records = await PredictionHistory.find({
      userId: req.userId,
    }).sort({ createdAt: -1 });

    return res.status(200).json({
      success: true,
      count: records.length,
      records,
    });
  } catch (error) {
    console.error("Fetch prediction history error:", error);

    return res.status(500).json({
      success: false,
      message: "Unable to fetch prediction history.",
    });
  }
};

// Delete one prediction
export const deletePrediction = async (req, res) => {
  try {
    const record = await PredictionHistory.findOneAndDelete({
      _id: req.params.id,
      userId: req.userId,
    });

    if (!record) {
      return res.status(404).json({
        success: false,
        message: "Prediction record not found.",
      });
    }

    return res.status(200).json({
      success: true,
      message: "Prediction deleted successfully.",
    });
  } catch (error) {
    console.error("Delete prediction error:", error);

    return res.status(500).json({
      success: false,
      message: "Unable to delete prediction.",
    });
  }
};

// Delete all predictions belonging to the logged-in user
export const clearPredictionHistory = async (req, res) => {
  try {
    const result = await PredictionHistory.deleteMany({
      userId: req.userId,
    });

    return res.status(200).json({
      success: true,
      message: "Prediction history cleared successfully.",
      deletedCount: result.deletedCount,
    });
  } catch (error) {
    console.error("Clear prediction history error:", error);

    return res.status(500).json({
      success: false,
      message: "Unable to clear prediction history.",
    });
  }
};
