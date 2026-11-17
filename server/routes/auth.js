
import { Router } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import crypto from "node:crypto";
import User from "../models/User.js";

import {
  getCookieOptions,
  requireAuth,
} from "../middleware/auth.js";

import { sendPasswordResetEmail } from "../services/emailService.js";

const router = Router();

const supportedCrops = [
  "Coffee",
  "Arecanut",
  "Ginger",
  "Cardamom",
];

function createSession(res, userId) {
  const token = jwt.sign(
    { userId: userId.toString() },
    process.env.JWT_SECRET,
    { expiresIn: process.env.JWT_EXPIRES_IN || "1d" }
  );

  res.cookie("kv_token", token, getCookieOptions());
}

function publicUser(user) {
  return {
    id: user._id.toString(),
    fullName: user.fullName,
    email: user.email,
    phone: user.phone || "",
    farmProfile: user.farmProfile || {},
    memberSince: user.createdAt || null,
  };
}

// POST /api/auth/register
router.post("/register", async (req, res, next) => {
  try {
    const { fullName, email, phone = "", password } = req.body || {};

    if (
      typeof fullName !== "string" ||
      typeof email !== "string" ||
      typeof password !== "string" ||
      typeof phone !== "string"
    ) {
      return res.status(400).json({
        success: false,
        message: "Please provide valid registration details.",
      });
    }

    const name = fullName.trim();
    const normalizedEmail = email.trim().toLowerCase();
    const normalizedPhone = phone.trim();

    if (name.length < 2 || name.length > 80) {
      return res.status(400).json({
        success: false,
        message: "Name must be between 2 and 80 characters.",
      });
    }

    if (
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail) ||
      normalizedEmail.length > 254
    ) {
      return res.status(400).json({
        success: false,
        message: "Please enter a valid email address.",
      });
    }

    if (normalizedPhone.length > 20) {
      return res.status(400).json({
        success: false,
        message: "Phone number is too long.",
      });
    }

    if (password.length < 8 || password.length > 72) {
      return res.status(400).json({
        success: false,
        message: "Password must be 8–72 characters long.",
      });
    }

    const passwordHash = await bcrypt.hash(password, 12);

    const user = await User.create({
      fullName: name,
      email: normalizedEmail,
      phone: normalizedPhone,
      passwordHash,
    });

    createSession(res, user._id);

    return res.status(201).json({
      success: true,
      message: "Account created successfully.",
      user: publicUser(user),
    });
  } catch (error) {
    if (error?.code === 11000) {
      return res.status(409).json({
        success: false,
        message: "An account with this email already exists.",
      });
    }

    next(error);
  }
});

// POST /api/auth/login
router.post("/login", async (req, res, next) => {
  try {
    const { email, password } = req.body || {};

    if (
      typeof email !== "string" ||
      typeof password !== "string" ||
      email.length > 254 ||
      password.length > 72
    ) {
      return res.status(400).json({
        success: false,
        message: "Please enter your email and password.",
      });
    }

    const user = await User.findOne({
      email: email.trim().toLowerCase(),
    }).select("+passwordHash");

    if (!user || !(await bcrypt.compare(password, user.passwordHash))) {
      return res.status(401).json({
        success: false,
        message: "Invalid email or password.",
      });
    }

    createSession(res, user._id);

    return res.json({
      success: true,
      message: "Signed in successfully.",
      user: publicUser(user),
    });
  } catch (error) {
    next(error);
  }
});

// GET /api/auth/me
router.get("/me", requireAuth, async (req, res, next) => {
  try {
    const user = await User.findById(req.userId);

    if (!user) {
      res.clearCookie("kv_token", getCookieOptions());

      return res.status(401).json({
        success: false,
        message: "Account not found. Please sign in again.",
      });
    }

    return res.json({
      success: true,
      user: publicUser(user),
    });
  } catch (error) {
    next(error);
  }
});

// GET /api/auth/profile
// Get the logged-in farmer's profile
router.get("/profile", requireAuth, async (req, res, next) => {
  try {
    const user = await User.findById(req.userId);

    if (!user) {
      return res.status(404).json({
        success: false,
        message: "Farmer account not found.",
      });
    }

    return res.json({
      success: true,
      message: "Farmer profile loaded successfully.",
      user: publicUser(user),
    });
  } catch (error) {
    next(error);
  }
});

// PUT /api/auth/profile
// Update the logged-in farmer's profile
router.put("/profile", requireAuth, async (req, res, next) => {
  try {
    const user = await User.findById(req.userId);

    if (!user) {
      return res.status(404).json({
        success: false,
        message: "Farmer account not found.",
      });
    }

    const {
      fullName,
      phone,
      farmProfile,
    } = req.body || {};

    if (fullName !== undefined) {
      if (
        typeof fullName !== "string" ||
        fullName.trim().length < 2 ||
        fullName.trim().length > 80
      ) {
        return res.status(400).json({
          success: false,
          message: "Name must be between 2 and 80 characters.",
        });
      }

      user.fullName = fullName.trim();
    }

    if (phone !== undefined) {
      if (
        typeof phone !== "string" ||
        phone.trim().length > 20 ||
        (phone.trim() && !/^[+\d\s()-]{7,20}$/.test(phone.trim()))
      ) {
        return res.status(400).json({
          success: false,
          message: "Please enter a valid phone number.",
        });
      }

      user.phone = phone.trim();
    }

    if (farmProfile !== undefined) {
      if (
        !farmProfile ||
        typeof farmProfile !== "object" ||
        Array.isArray(farmProfile)
      ) {
        return res.status(400).json({
          success: false,
          message: "Invalid farm profile details.",
        });
      }

      const allowedFields = [
        "location",
        "farmName",
        "farmArea",
        "landType",
        "soilType",
        "waterSource",
        "farmingType",
        "primaryCrops",
        "interestedCrops",
        "language",
        "emailNotifications",
        "smsNotifications",
        "weatherAlerts",
        "recommendations",
      ];

      for (const field of Object.keys(farmProfile)) {
        if (!allowedFields.includes(field)) {
          return res.status(400).json({
            success: false,
            message: `Field '${field}' cannot be updated.`,
          });
        }
      }

      const currentProfile = user.farmProfile?.toObject
        ? user.farmProfile.toObject()
        : { ...(user.farmProfile || {}) };

      const updatedProfile = {
        ...currentProfile,
        ...farmProfile,
      };

      for (const field of [
        "location",
        "farmName",
        "landType",
        "soilType",
        "waterSource",
        "farmingType",
      ]) {
        if (
          updatedProfile[field] !== undefined &&
          typeof updatedProfile[field] !== "string"
        ) {
          return res.status(400).json({
            success: false,
            message: `Invalid value for ${field}.`,
          });
        }
      }

      if (
        updatedProfile.farmArea !== null &&
        updatedProfile.farmArea !== "" &&
        updatedProfile.farmArea !== undefined &&
        (!Number.isFinite(Number(updatedProfile.farmArea)) ||
          Number(updatedProfile.farmArea) < 0)
      ) {
        return res.status(400).json({
          success: false,
          message: "Farm area must be a valid non-negative number.",
        });
      }

      for (const field of ["primaryCrops", "interestedCrops"]) {
        if (
          !Array.isArray(updatedProfile[field]) ||
          !updatedProfile[field].every(
            (crop) =>
              typeof crop === "string" && supportedCrops.includes(crop)
          )
        ) {
          return res.status(400).json({
            success: false,
            message: `Invalid ${field} selection.`,
          });
        }
      }

      const validLanguages = [
        "English",
        "Kannada",
        "English / Kannada",
      ];

      if (!validLanguages.includes(updatedProfile.language)) {
        return res.status(400).json({
          success: false,
          message: "Invalid language preference.",
        });
      }

      for (const field of [
        "emailNotifications",
        "smsNotifications",
        "weatherAlerts",
        "recommendations",
      ]) {
        if (typeof updatedProfile[field] !== "boolean") {
          return res.status(400).json({
            success: false,
            message: `Invalid setting for ${field}.`,
          });
        }
      }

      user.farmProfile = updatedProfile;
    }

    await user.save();

    return res.json({
      success: true,
      message: "Farmer profile updated successfully.",
      user: publicUser(user),
    });
  } catch (error) {
    next(error);
  }
});

// POST /api/auth/logout
router.post("/logout", (_req, res) => {
  res.clearCookie("kv_token", getCookieOptions());

  return res.json({
    success: true,
    message: "Signed out successfully.",
  });
});

// POST /api/auth/forgot-password
router.post("/forgot-password", async (req, res, next) => {
  try {
    const email = req.body?.email;

    const genericResponse = {
      success: true,
      message:
        "If an account exists for that email, a password reset link will be sent.",
    };

    if (
      typeof email !== "string" ||
      email.length > 254 ||
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())
    ) {
      return res.status(200).json(genericResponse);
    }

    const user = await User.findOne({
      email: email.trim().toLowerCase(),
    });

    if (!user) {
      return res.status(200).json(genericResponse);
    }

    const rawToken = crypto.randomBytes(32).toString("hex");

    const tokenHash = crypto
      .createHash("sha256")
      .update(rawToken)
      .digest("hex");

    user.resetPasswordTokenHash = tokenHash;
    user.resetPasswordExpires = new Date(Date.now() + 15 * 60 * 1000);

    await user.save();

    const frontendUrl = process.env.FRONTEND_URL;

    if (!frontendUrl) {
      throw new Error("FRONTEND_URL is missing from server/.env");
    }

    const resetUrl =
      `${frontendUrl.replace(/\/+$/, "")}/reset-password?token=${rawToken}`;

    try {
      await sendPasswordResetEmail(user.email, resetUrl);
    } catch (emailError) {
      user.resetPasswordTokenHash = undefined;
      user.resetPasswordExpires = undefined;

      await user.save();

      throw emailError;
    }

    return res.status(200).json(genericResponse);
  } catch (error) {
    next(error);
  }
});

// POST /api/auth/reset-password
router.post("/reset-password", async (req, res, next) => {
  try {
    const { token, password } = req.body || {};

    if (
      typeof token !== "string" ||
      !/^[a-f0-9]{64}$/i.test(token) ||
      typeof password !== "string" ||
      password.length < 8 ||
      password.length > 72
    ) {
      return res.status(400).json({
        success: false,
        message: "Invalid or expired reset link, or invalid password.",
      });
    }

    const tokenHash = crypto
      .createHash("sha256")
      .update(token)
      .digest("hex");

    const user = await User.findOne({
      resetPasswordTokenHash: tokenHash,
      resetPasswordExpires: { $gt: new Date() },
    }).select("+resetPasswordTokenHash +resetPasswordExpires");

    if (!user) {
      return res.status(400).json({
        success: false,
        message: "Invalid or expired reset link. Request a new one.",
      });
    }

    user.passwordHash = await bcrypt.hash(password, 12);
    user.resetPasswordTokenHash = undefined;
    user.resetPasswordExpires = undefined;

    await user.save();

    return res.json({
      success: true,
      message: "Password reset successfully. Please sign in.",
    });
  } catch (error) {
    next(error);
  }
});

export default router;
