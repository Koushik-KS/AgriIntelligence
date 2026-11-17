
import mongoose from "mongoose";

const supportedCrops = [
  "Coffee",
  "Arecanut",
  "Ginger",
  "Cardamom",
];

const userSchema = new mongoose.Schema(
  {
    fullName: {
      type: String,
      required: true,
      trim: true,
      minlength: 2,
      maxlength: 80,
    },

    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
      maxlength: 254,
      match: [/^[^\s@]+@[^\s@]+\.[^\s@]+$/, "Enter a valid email address"],
    },

    phone: {
      type: String,
      trim: true,
      default: "",
      maxlength: 20,
    },

    passwordHash: {
      type: String,
      required: true,
      select: false,
    },

    // Farmer profile and farm information
    farmProfile: {
      location: { type: String, trim: true, default: "" },
      farmName: { type: String, trim: true, default: "" },
      farmArea: { type: Number, min: 0, default: null },
      landType: { type: String, default: "" },
      soilType: { type: String, default: "" },
      waterSource: { type: String, default: "" },
      farmingType: { type: String, default: "" },

      primaryCrops: {
        type: [{ type: String, enum: supportedCrops }],
        default: [],
      },

      interestedCrops: {
        type: [{ type: String, enum: supportedCrops }],
        default: [],
      },

      language: {
        type: String,
        enum: ["English", "Kannada", "English / Kannada"],
        default: "English",
      },

      emailNotifications: { type: Boolean, default: true },
      smsNotifications: { type: Boolean, default: false },
      weatherAlerts: { type: Boolean, default: true },
      recommendations: { type: Boolean, default: true },
    },

    // Store only the hash of the reset token.
    resetPasswordTokenHash: {
      type: String,
      default: undefined,
      select: false,
    },

    resetPasswordExpires: {
      type: Date,
      default: undefined,
      select: false,
    },
  },
  {
    timestamps: true,
    versionKey: false,
  }
);

userSchema.set("toJSON", {
  transform(_document, returnedObject) {
    delete returnedObject.passwordHash;
    delete returnedObject.resetPasswordTokenHash;
    delete returnedObject.resetPasswordExpires;
    return returnedObject;
  },
});

const User = mongoose.model("User", userSchema);

export default User;
