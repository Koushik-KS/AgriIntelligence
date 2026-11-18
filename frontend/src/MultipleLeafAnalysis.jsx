import { useEffect, useMemo, useRef, useState } from "react";
import {
  FaLeaf, FaImages, FaCloudUploadAlt, FaTimes, FaCheckCircle,
  FaExclamationTriangle, FaDownload, FaSearch, FaChartBar,
  FaQuestionCircle, FaSeedling, FaHistory, FaFileAlt, FaShieldAlt,
  FaInfoCircle, FaChevronDown, FaBars,
} from "react-icons/fa";
import "./MultipleLeafAnalysis.css";

const MAX_IMAGES = 20;
const MAX_FILE_SIZE = 5 * 1024 * 1024;
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const HISTORY_KEY = "kisanvision_multi_image_history_v1";
const CROPS = ["Coffee", "Arecanut", "Cardamom", "Ginger"];

const API_CONFIG = {
  Coffee: {
    url: import.meta.env.VITE_COFFEE_API_URL || "https://kisanvision-coffee-api.onrender.com",
    endpoint: "/predict/coffee",
  },
  Arecanut: {
    url: import.meta.env.VITE_ARECANUT_API_URL || "https://kisanvision-arecanut-api.onrender.com",
    endpoint: "/predict/arecanut",
  },
  Cardamom: {
    url: import.meta.env.VITE_CARDAMOM_API_URL || "https://kisanvision-cardamom-api.onrender.com",
    endpoint: "/predict/cardamom",
  },
  Ginger: {
    url: import.meta.env.VITE_GINGER_API_URL || "https://kisanvision-ginger-api.onrender.com",
    endpoint: "/predict/ginger",
  },
};
const menuItems = [
  { label: "Analyze Multiple Leaves", icon: FaImages, target: "mla-upload" },
  { label: "Supported Crops", icon: FaSeedling, target: "mla-crops" },
  { label: "Result Summary", icon: FaChartBar, target: "mla-summary" },
  { label: "Download Report", icon: FaDownload, target: "mla-results" },
  { label: "Upload History", icon: FaHistory, target: "mla-history" },
  { label: "FAQs", icon: FaQuestionCircle, target: "mla-faqs" },
];

const faqs = [
  {
    question: "How many images can I upload?",
    answer: "You can select up to 20 images in one batch. Each image can be up to 5 MB.",
  },
  {
    question: "Which image formats are supported?",
    answer: "JPG, PNG and WebP images are supported.",
  },
  {
    question: "How is the crop selected?",
    answer: "Choose Coffee, Arecanut, Cardamom or Ginger for every image. The selected crop decides which prediction API receives that image.",
  },
  {
    question: "Does the report show disease severity?",
    answer: "No. The connected APIs return a predicted class and confidence. They do not provide a validated disease-severity measurement.",
  },
  {
    question: "Are previous results saved?",
    answer: "Upload history stores result summaries in this browser's local storage. It does not store the original image files.",
  },
];

const normalise = (value = "") =>
  String(value).toUpperCase().replace(/[^A-Z0-9]/g, "");

const isHealthyClass = (label = "") => normalise(label).includes("HEALTHY");

function readHistory() {
  try {
    const saved = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

/*
 * The environment variable may contain either:
 *   http://127.0.0.1:8000
 * or the full endpoint:
 *   http://127.0.0.1:8000/predict/coffee
 * This function prevents the duplicated URL seen in the terminal log.
 */
function buildPredictionUrl(crop) {
  const config = API_CONFIG[crop];
  if (!config) throw new Error(`No API configuration found for ${crop}.`);

  const base = String(config.url).trim().replace(/\/+$/, "");
  const endpoint = config.endpoint;
  const cleanBase = base.toLowerCase().endsWith(endpoint.toLowerCase())
    ? base.slice(0, -endpoint.length).replace(/\/+$/, "")
    : base;

  return `${cleanBase}${endpoint}`;
}

function MultipleLeafAnalysis() {
  const [images, setImages] = useState([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [threshold, setThreshold] = useState("50");
  const [diseasedOnly, setDiseasedOnly] = useState(false);
  const [groupByCrop, setGroupByCrop] = useState(true);
  const [activeSection, setActiveSection] = useState("mla-upload");
  const [openFaq, setOpenFaq] = useState(0);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [history, setHistory] = useState(readHistory);
  const [selectedDetails, setSelectedDetails] = useState(null);

  const inputRef = useRef(null);
  const idRef = useRef(0);
  const imagesRef = useRef([]);

  useEffect(() => {
    imagesRef.current = images;
  }, [images]);

  useEffect(() => {
    return () => {
      imagesRef.current.forEach((image) => URL.revokeObjectURL(image.preview));
    };
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 30)));
    } catch {
      // Browser storage may be unavailable or full.
    }
  }, [history]);

  const addImages = (fileList) => {
    const files = Array.from(fileList || []);
    if (!files.length) return;

    setError("");
    setNotice("");

    const accepted = [];
    const rejected = [];

    files.forEach((file) => {
      if (!ALLOWED_TYPES.includes(file.type)) {
        rejected.push(`${file.name}: unsupported file type.`);
      } else if (file.size > MAX_FILE_SIZE) {
        rejected.push(`${file.name}: file exceeds 5 MB.`);
      } else {
        accepted.push(file);
      }
    });

    setImages((current) => {
      const remaining = MAX_IMAGES - current.length;
      const filesToAdd = accepted.slice(0, Math.max(0, remaining));

      if (accepted.length > remaining) {
        rejected.push(`Only ${MAX_IMAGES} images can be selected.`);
      }

      const newImages = filesToAdd.map((file) => ({
        id: ++idRef.current,
        file,
        preview: URL.createObjectURL(file),
        crop: "",
        status: "pending",
        result: null,
        apiError: "",
      }));

      if (newImages.length) {
        setNotice(
          `${newImages.length} image(s) added. Select the crop for every image, then start analysis.`
        );
      }
      if (rejected.length) setError(rejected.join(" "));

      return [...current, ...newImages];
    });

    if (inputRef.current) inputRef.current.value = "";
  };

  const updateCrop = (id, crop) => {
    setImages((current) =>
      current.map((image) =>
        image.id === id
          ? { ...image, crop, result: null, apiError: "", status: "pending" }
          : image
      )
    );
  };

  const removeImage = (id) => {
    setImages((current) => {
      const image = current.find((item) => item.id === id);
      if (image) URL.revokeObjectURL(image.preview);
      return current.filter((item) => item.id !== id);
    });
    setError("");
    setNotice("Selected image removed.");
  };

  const clearAll = () => {
    images.forEach((image) => URL.revokeObjectURL(image.preview));
    setImages([]);
    setError("");
    setNotice("All selected images cleared.");
    setSelectedDetails(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const goToSection = (target) => {
    setActiveSection(target);
    setMobileSidebarOpen(false);
    document.getElementById(target)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const analyzeImages = async () => {
    if (!images.length || isAnalyzing) return;

    const unselected = images.filter((image) => !image.crop);
    if (unselected.length) {
      setError(
        `Please select a crop for every image. ${unselected.length} image(s) still need a crop selection.`
      );
      return;
    }

    setError("");
    setNotice("");
    setIsAnalyzing(true);

    const batch = [...images];

    setImages((current) =>
      current.map((image) => ({
        ...image,
        status: "processing",
        result: null,
        apiError: "",
      }))
    );

    const successful = [];

    await Promise.all(
      batch.map(async (image) => {
        try {
          const requestUrl = buildPredictionUrl(image.crop);
          const formData = new FormData();
          formData.append("file", image.file);

          const response = await fetch(requestUrl, {
            method: "POST",
            body: formData,
          });

          let payload;
          try {
            payload = await response.json();
          } catch {
            throw new Error(
              `${image.crop} API returned an unreadable response (HTTP ${response.status}).`
            );
          }

          if (!response.ok) {
            const detail =
              typeof payload?.detail === "string"
                ? payload.detail
                : payload?.message || `HTTP ${response.status}`;
            throw new Error(detail);
          }

          if (
            !payload?.success ||
            !payload?.predicted_class ||
            !Number.isFinite(Number(payload?.confidence))
          ) {
            throw new Error("The API response is missing prediction details.");
          }

          const result = {
            crop: payload.crop || image.crop,
            predictedClass: payload.predicted_class,
            confidence: Number(payload.confidence),
            probabilities: payload.probabilities || {},
            warning: payload.warning || "",
          };

          successful.push({ image, result });

          setImages((current) =>
            current.map((item) =>
              item.id === image.id
                ? { ...item, status: "complete", result, apiError: "" }
                : item
            )
          );
        } catch (apiError) {
          const message =
            apiError?.message ||
            "Prediction failed. Check that the selected crop API is running.";

          setImages((current) =>
            current.map((item) =>
              item.id === image.id
                ? { ...item, status: "error", result: null, apiError: message }
                : item
            )
          );
        }
      })
    );

    const failed = batch.length - successful.length;

    if (successful.length) {
      setHistory((current) =>
        [
          {
            id: Date.now(),
            date: new Date().toISOString(),
            total: batch.length,
            successful: successful.length,
            failed,
            results: successful.map(({ image, result }) => ({
              filename: image.file.name,
              crop: result.crop,
              predictedClass: result.predictedClass,
              confidence: result.confidence,
            })),
          },
          ...current,
        ].slice(0, 30)
      );
    }

    setNotice(
      `Analysis finished: ${successful.length} successful, ${failed} failed. Review each result and confidence.`
    );
    setIsAnalyzing(false);
    setActiveSection("mla-results");
    document.getElementById("mla-results")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  const thresholdValue = threshold === "default" ? 50 : Number(threshold);

  const completedImages = useMemo(
    () => images.filter((image) => image.status === "complete" && image.result),
    [images]
  );

  const visibleResults = useMemo(
    () =>
      completedImages.filter((image) => {
        if (image.result.confidence < thresholdValue) return false;
        if (diseasedOnly && isHealthyClass(image.result.predictedClass)) {
          return false;
        }
        return true;
      }),
    [completedImages, thresholdValue, diseasedOnly]
  );

  const displayedImages = useMemo(() => {
    const filtered = images.filter((image) => {
      if (image.status !== "complete" || !image.result) return true;
      if (image.result.confidence < thresholdValue) return false;
      if (diseasedOnly && isHealthyClass(image.result.predictedClass)) {
        return false;
      }
      return true;
    });

    return groupByCrop
      ? [...filtered].sort((a, b) => a.crop.localeCompare(b.crop))
      : filtered;
  }, [images, thresholdValue, diseasedOnly, groupByCrop]);

  const healthyCount = completedImages.filter((image) =>
    isHealthyClass(image.result.predictedClass)
  ).length;
  const diseasedCount = completedImages.length - healthyCount;
  const failedCount = images.filter((image) => image.status === "error").length;
  const totalBytes = images.reduce((sum, image) => sum + image.file.size, 0);

  const cropCounts = CROPS.map((crop) => ({
    crop,
    count: completedImages.filter(
      (image) => image.result.crop.toLowerCase() === crop.toLowerCase()
    ).length,
  }));

  const downloadReport = () => {
    if (!images.length) {
      setError("Upload at least one image before downloading the report.");
      return;
    }

    const escapeCsv = (value) =>
      `"${String(value ?? "").replace(/"/g, '""')}"`;

    const rows = [
      [
        "Image filename",
        "Selected crop",
        "Predicted crop",
        "Predicted class",
        "Confidence (%)",
        "Status",
        "Warning / Error",
      ],
    ];

    images.forEach((image) =>
      rows.push([
        image.file.name,
        image.crop || "Not selected",
        image.result?.crop || "",
        image.result?.predictedClass || "",
        image.result?.confidence ?? "",
        image.status === "complete"
          ? "Completed"
          : image.status === "error"
            ? "Failed"
            : image.status === "processing"
              ? "Processing"
              : "Not analyzed",
        image.result?.warning || image.apiError || "",
      ])
    );

    const csv = rows.map((row) => row.map(escapeCsv).join(",")).join("\r\n");
    const blob = new Blob(["\uFEFF" + csv], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "kisanvision-multi-image-analysis-report.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setNotice("Prediction report downloaded.");
    setError("");
  };

  const openDetails = (image) => setSelectedDetails(image);

  return (
    <div className="mla-page">
      <aside
        className={`mla-left-sidebar ${
          mobileSidebarOpen ? "mla-sidebar-open" : ""
        }`}
      >
        <div className="mla-sidebar-title">
          <FaSeedling />
          <strong>Multi-Image Analysis</strong>
        </div>

        <nav className="mla-side-nav" aria-label="Multi-image analysis sections">
          {menuItems.map(({ label, icon: Icon, target }) => (
            <button
              type="button"
              key={target}
              className={
                activeSection === target
                  ? "mla-side-link active"
                  : "mla-side-link"
              }
              onClick={() => goToSection(target)}
            >
              <Icon />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="mla-sidebar-landscape">
          <div className="mla-landscape-copy">
            <strong>
              Analyse More
              <br />
              Get Clear Insights
              <br />
              Healthier Crops
              <br />
              Better Yields
            </strong>
          </div>
        </div>
      </aside>

      <div className="mla-workspace">
        <header className="mla-page-heading">
          <button
            type="button"
            className="mla-mobile-sidebar-toggle"
            onClick={() => setMobileSidebarOpen((open) => !open)}
            aria-label="Toggle analysis menu"
          >
            <FaBars />
          </button>
          <div className="mla-heading-icon">
            <FaImages />
          </div>
          <div className="mla-heading-copy">
            <h1>Multi-Image Analysis</h1>
            <p>
              Analyse multiple leaf images using the four crop-specific trained
              models.
            </p>
          </div>
          <div className="mla-breadcrumb">Home&nbsp; › &nbsp;Multi-Image Analysis</div>
        </header>

        {error && (
          <div className="mla-alert mla-alert-error" role="alert">
            <FaExclamationTriangle />
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError("")}
              aria-label="Dismiss error"
            >
              <FaTimes />
            </button>
          </div>
        )}

        {notice && (
          <div className="mla-alert mla-alert-info" role="status">
            <FaInfoCircle />
            <span>{notice}</span>
            <button
              type="button"
              onClick={() => setNotice("")}
              aria-label="Dismiss message"
            >
              <FaTimes />
            </button>
          </div>
        )}

        <section className="mla-top-grid" id="mla-upload">
          <div className="mla-panel mla-upload-panel">
            <div
              className="mla-dropzone"
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                addImages(event.dataTransfer.files);
              }}
            >
              <FaCloudUploadAlt className="mla-cloud-icon" />
              <strong>Drag &amp; drop multiple leaf images here</strong>
              <span>or</span>
              <button
                type="button"
                className="mla-primary-button"
                onClick={() => inputRef.current?.click()}
                disabled={images.length >= MAX_IMAGES || isAnalyzing}
              >
                <FaFileAlt /> Choose Files
              </button>
              <input
                ref={inputRef}
                type="file"
                hidden
                multiple
                accept="image/jpeg,image/png,image/webp"
                onChange={(event) => addImages(event.target.files)}
              />
              <small>
                Supports: JPG, PNG, WebP
                <br />
                (Max 20 images, each up to 5 MB)
              </small>
            </div>
          </div>

          <div className="mla-panel mla-uploaded-panel">
            <div className="mla-panel-heading">
              <h2>
                <FaImages /> Uploaded Images ({images.length})
              </h2>
              <button
                type="button"
                className="mla-clear-button"
                onClick={clearAll}
                disabled={!images.length || isAnalyzing}
              >
                Clear All
              </button>
            </div>

            {images.length ? (
              <div className="mla-thumbnail-grid">
                {images.map((image, index) => (
                  <article className="mla-thumbnail" key={image.id}>
                    <div className="mla-thumbnail-image">
                      <img
                        src={image.preview}
                        alt={`Uploaded leaf ${index + 1}`}
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(image.id)}
                        disabled={isAnalyzing}
                        aria-label={`Remove ${image.file.name}`}
                        title="Remove image"
                      >
                        <FaTimes />
                      </button>
                    </div>
                    <span title={image.file.name}>{image.file.name}</span>
                    <label className="mla-crop-select-label">
                      Crop
                      <select
                        value={image.crop}
                        disabled={isAnalyzing}
                        onChange={(event) =>
                          updateCrop(image.id, event.target.value)
                        }
                      >
                        <option value="">Select crop</option>
                        {CROPS.map((crop) => (
                          <option key={crop} value={crop}>
                            {crop}
                          </option>
                        ))}
                      </select>
                    </label>
                    <small
                      className={`mla-image-status mla-status-${image.status}`}
                    >
                      {image.status === "complete"
                        ? "Analysis complete"
                        : image.status === "processing"
                          ? "Analyzing..."
                          : image.status === "error"
                            ? "Analysis failed"
                            : image.crop
                              ? "Ready"
                              : "Select crop"}
                    </small>
                  </article>
                ))}
              </div>
            ) : (
              <div className="mla-mini-empty">
                <FaImages />
                <span>Your uploaded images will appear here.</span>
              </div>
            )}
          </div>

          <div className="mla-panel mla-settings-panel">
            <h2>
              <FaSeedling /> Analysis Settings <span>(Optional)</span>
            </h2>
            <label className="mla-setting-row" htmlFor="mla-threshold">
              <span>Confidence Threshold</span>
              <span className="mla-select-wrap">
                <select
                  id="mla-threshold"
                  value={threshold}
                  onChange={(event) => setThreshold(event.target.value)}
                >
                  <option value="default">Default (50%)</option>
                  <option value="30">30%</option>
                  <option value="50">50%</option>
                  <option value="70">70%</option>
                  <option value="90">90%</option>
                </select>
                <FaChevronDown />
              </span>
            </label>

            <div className="mla-setting-row">
              <span>Show Only Diseased Leaves</span>
              <button
                type="button"
                className={`mla-switch ${diseasedOnly ? "on" : ""}`}
                role="switch"
                aria-checked={diseasedOnly}
                onClick={() => setDiseasedOnly((value) => !value)}
                aria-label="Show only diseased leaves"
              >
                <span />
              </button>
            </div>

            <div className="mla-setting-row">
              <span>Group by Crop</span>
              <button
                type="button"
                className={`mla-switch ${groupByCrop ? "on" : ""}`}
                role="switch"
                aria-checked={groupByCrop}
                onClick={() => setGroupByCrop((value) => !value)}
                aria-label="Group by crop"
              >
                <span />
              </button>
            </div>

            <button
              type="button"
              className="mla-start-button"
              disabled={
                !images.length ||
                isAnalyzing ||
                images.some((image) => !image.crop)
              }
              onClick={analyzeImages}
            >
              <FaSearch />{" "}
              {isAnalyzing ? "Analyzing Images..." : "Start Analysis"}
            </button>
            <p className="mla-settings-note">
              Select the correct crop for every image. Each crop uses its own
              prediction API. Filters affect displayed results, not predictions.
            </p>
          </div>
        </section>

        <section className="mla-results-grid">
          <div className="mla-results-column">
            <section className="mla-panel mla-results-panel" id="mla-results">
              <div className="mla-panel-heading mla-results-heading">
                <h2>
                  <FaShieldAlt /> Analysis Results{" "}
                  <span>({visibleResults.length} matching results)</span>
                </h2>
                <button
                  type="button"
                  className="mla-report-button"
                  onClick={downloadReport}
                  disabled={!images.length}
                >
                  <FaDownload /> Download Report
                </button>
              </div>

              <div className="mla-table-scroll">
                <table className="mla-results-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Image</th>
                      <th>Crop Identified</th>
                      <th>Disease / Health Status</th>
                      <th>Confidence</th>
                      <th>Severity</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedImages.length ? (
                      displayedImages.map((image, index) => (
                        <tr key={image.id}>
                          <td>{index + 1}</td>
                          <td>
                            <img
                              className="mla-table-thumb"
                              src={image.preview}
                              alt={image.file.name}
                            />
                          </td>
                          <td>{image.crop || "Not selected"}</td>
                          <td>
                            {image.status === "complete" ? (
                              <span
                                className={
                                  isHealthyClass(image.result.predictedClass)
                                    ? "mla-pending-label"
                                    : "mla-pending-badge"
                                }
                              >
                                {image.result.predictedClass}
                              </span>
                            ) : image.status === "error" ? (
                              <span className="mla-pending-badge">API error</span>
                            ) : (
                              <span className="mla-pending-label">
                                {image.status === "processing"
                                  ? "Processing"
                                  : "Not analyzed"}
                              </span>
                            )}
                            {image.apiError && <small>{image.apiError}</small>}
                          </td>
                          <td>
                            {image.result
                              ? `${image.result.confidence.toFixed(2)}%`
                              : "—"}
                          </td>
                          <td>Not provided</td>
                          <td>
                            <button
                              type="button"
                              className="mla-view-button"
                              onClick={() => openDetails(image)}
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="7" className="mla-table-empty">
                          <FaImages />
                          <strong>No matching results</strong>
                          <span>
                            Upload images and run analysis, or adjust your
                            filters.
                          </span>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <div className="mla-model-notice">
                <FaInfoCircle />
                Confidence is the model's prediction score, not a confirmed
                diagnosis. Severity is not supplied by these APIs.
              </div>
            </section>

            <section className="mla-panel mla-next-steps">
              <h2>
                <FaCheckCircle /> Next Steps
              </h2>
              <div className="mla-next-grid">
                <div>
                  <FaLeaf />
                  <span>Review the predicted class and confidence for each image.</span>
                </div>
                <div>
                  <FaShieldAlt />
                  <span>Verify predictions with an agricultural expert.</span>
                </div>
                <div>
                  <FaFileAlt />
                  <span>Download the CSV report for your records.</span>
                </div>
                <div>
                  <FaSearch />
                  <span>Use crop-appropriate expert guidance before treatment.</span>
                </div>
              </div>
            </section>
          </div>

          <aside className="mla-summary-column">
            <section className="mla-panel mla-summary-panel" id="mla-summary">
              <h2>
                <FaChartBar /> Summary
              </h2>
              <div className="mla-summary-stats">
                <div>
                  <FaImages />
                  <span>Total Images</span>
                  <strong>{images.length}</strong>
                </div>
                <div>
                  <FaLeaf />
                  <span>Healthy Leaves</span>
                  <strong>{healthyCount}</strong>
                </div>
                <div>
                  <FaExclamationTriangle />
                  <span>Diseased Leaves</span>
                  <strong>{diseasedCount}</strong>
                </div>
              </div>
              <p className="mla-summary-note">
                Completed predictions: {completedImages.length}. Failed
                predictions: {failedCount}.
              </p>
              <div className="mla-crop-summary" id="mla-crops">
                <h3>Crop-wise Breakdown</h3>
                {cropCounts.map(({ crop, count }) => (
                  <div className="mla-crop-row" key={crop}>
                    <span>{crop}</span>
                    <strong>{count}</strong>
                  </div>
                ))}
                <h3 className="mla-supported-heading">Supported Crops</h3>
                {CROPS.map((crop) => (
                  <div className="mla-crop-row" key={crop}>
                    <span>{crop}</span>
                    <span className="mla-no-data">Available</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="mla-panel mla-insights-panel">
              <h2>
                <FaChartBar /> Key Insights
              </h2>
              <div className="mla-insight-item">
                <FaInfoCircle />
                <p>
                  {images.length
                    ? `${images.length} image(s) in this batch; ${completedImages.length} analyzed successfully.`
                    : "Upload leaf images to begin."}
                </p>
              </div>
              <div className="mla-insight-item">
                <FaShieldAlt />
                <p>
                  {failedCount
                    ? `${failedCount} image(s) failed. Check their API error messages.`
                    : "Review predictions before making crop-treatment decisions."}
                </p>
              </div>
              <div className="mla-insight-item">
                <FaCloudUploadAlt />
                <p>
                  Current file size: {(totalBytes / (1024 * 1024)).toFixed(2)} MB.
                </p>
              </div>
              <p className="mla-insights-footnote">
                {diseasedOnly
                  ? "Showing diseased predictions only. "
                  : "Healthy and diseased predictions are included. "}
                {groupByCrop
                  ? "Results are grouped by crop. "
                  : "Crop grouping is off. "}
                Confidence filter: {thresholdValue}%.
              </p>
            </section>
          </aside>
        </section>

        <section className="mla-panel mla-history-panel" id="mla-history">
          <div className="mla-panel-heading">
            <h2>
              <FaHistory /> Upload History
            </h2>
            <button
              type="button"
              className="mla-clear-button"
              onClick={() => {
                setHistory([]);
                setNotice("Upload history cleared from this browser.");
              }}
              disabled={!history.length}
            >
              Clear History
            </button>
          </div>
          {history.length ? (
            <div className="mla-table-scroll">
              <table className="mla-results-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Total</th>
                    <th>Successful</th>
                    <th>Failed</th>
                    <th>Prediction details</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((entry) => (
                    <tr key={entry.id}>
                      <td>{new Date(entry.date).toLocaleString()}</td>
                      <td>{entry.total}</td>
                      <td>{entry.successful}</td>
                      <td>{entry.failed}</td>
                      <td>
                        {entry.results
                          .map(
                            (result) =>
                              `${result.filename}: ${result.crop} / ${result.predictedClass} (${result.confidence}%)`
                          )
                          .join("; ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No previous analysis sessions are saved in this browser yet.</p>
          )}
        </section>

        <section className="mla-panel mla-faq-panel" id="mla-faqs">
          <h2>
            <FaQuestionCircle /> Frequently Asked Questions
          </h2>
          {faqs.map((faq, index) => (
            <div className="mla-faq-item" key={faq.question}>
              <button
                type="button"
                onClick={() =>
                  setOpenFaq(openFaq === index ? -1 : index)
                }
                aria-expanded={openFaq === index}
              >
                {faq.question}
                <FaChevronDown
                  className={openFaq === index ? "rotated" : ""}
                />
              </button>
              {openFaq === index && <p>{faq.answer}</p>}
            </div>
          ))}
        </section>

        <footer className="mla-footer">
          KisanVision AI · BAI586 academic mini-project
          <span>Four crop-specific APIs · Predictions require verification</span>
        </footer>
      </div>

      {selectedDetails && (
        <div
          className="mla-details-backdrop"
          role="presentation"
          onClick={() => setSelectedDetails(null)}
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            background: "rgba(0,0,0,0.55)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "20px",
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="mla-details-title"
            onClick={(event) => event.stopPropagation()}
            style={{
              background: "#fff",
              color: "#24352d",
              width: "min(520px, 100%)",
              maxHeight: "85vh",
              overflowY: "auto",
              borderRadius: "14px",
              padding: "24px",
              boxShadow: "0 18px 60px rgba(0,0,0,0.25)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <h2 id="mla-details-title" style={{ margin: 0 }}>
                Image Analysis Details
              </h2>
              <button
                type="button"
                onClick={() => setSelectedDetails(null)}
                aria-label="Close details"
                style={{
                  border: 0,
                  background: "transparent",
                  fontSize: "22px",
                  cursor: "pointer",
                }}
              >
                <FaTimes />
              </button>
            </div>

            <img
              src={selectedDetails.preview}
              alt={selectedDetails.file.name}
              style={{
                width: "100%",
                maxHeight: "220px",
                objectFit: "contain",
                margin: "16px 0",
                borderRadius: "8px",
                background: "#f3f6f4",
              }}
            />

            <p><strong>Filename:</strong> {selectedDetails.file.name}</p>
            <p><strong>Selected crop:</strong> {selectedDetails.crop || "Not selected"}</p>
            <p>
              <strong>Status:</strong>{" "}
              {selectedDetails.status === "complete"
                ? "Completed"
                : selectedDetails.status === "error"
                  ? "Failed"
                  : selectedDetails.status === "processing"
                    ? "Processing"
                    : "Not analyzed"}
            </p>

            {selectedDetails.result ? (
              <>
                <p><strong>Predicted class:</strong> {selectedDetails.result.predictedClass}</p>
                <p><strong>Confidence:</strong> {selectedDetails.result.confidence.toFixed(2)}%</p>
                {selectedDetails.result.warning && (
                  <p><strong>Model warning:</strong> {selectedDetails.result.warning}</p>
                )}
                {selectedDetails.result.probabilities &&
                  Object.keys(selectedDetails.result.probabilities).length > 0 && (
                    <>
                      <h3>Class probabilities</h3>
                      {Object.entries(selectedDetails.result.probabilities).map(
                        ([label, value]) => (
                          <p key={label}>
                            <strong>{label}:</strong> {Number(value).toFixed(2)}%
                          </p>
                        )
                      )}
                    </>
                  )}
                <p><strong>Severity:</strong> Not provided by the prediction API.</p>
              </>
            ) : (
              <p style={{ color: "#a35b16" }}>
                <strong>Details:</strong>{" "}
                {selectedDetails.apiError ||
                  "This image has not been analyzed yet."}
              </p>
            )}

            <button
              type="button"
              onClick={() => setSelectedDetails(null)}
              style={{
                marginTop: "12px",
                padding: "10px 18px",
                border: 0,
                borderRadius: "8px",
                background: "#087653",
                color: "#fff",
                cursor: "pointer",
              }}
            >
              Close
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

export default MultipleLeafAnalysis;
