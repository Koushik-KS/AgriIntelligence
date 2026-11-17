import { useEffect, useMemo, useState } from "react";
import {
  FaHistory,
  FaMicroscope,
  FaFileExport,
  FaTrashAlt,
  FaQuestionCircle,
  FaSearch,
  FaFilter,
  FaCalendarAlt,
  FaEye,
  FaDownload,
  FaTimes,
  FaInfoCircle,
  FaSeedling,
  FaChevronDown,
  FaClipboardList,
} from "react-icons/fa";
import "./PredictionHistory.css";

const HISTORY_API_URL =
  (import.meta.env.VITE_AUTH_API_URL || "http://localhost:5000/api") +
  "/history";

const historyNavigation = [
  { label: "All Analyses", icon: FaHistory, value: "All" },
  {
    label: "Disease Detection",
    icon: FaMicroscope,
    value: "Disease Detection",
  },
  { label: "Export Reports", icon: FaFileExport, value: "Export Reports" },
  { label: "Delete Records", icon: FaTrashAlt, value: "Delete Records" },
  { label: "FAQs", icon: FaQuestionCircle, value: "FAQs" },
];

function PredictionHistory() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  const [activeCategory, setActiveCategory] = useState("All");
  const [search, setSearch] = useState("");
  const [analysisType, setAnalysisType] = useState("All Types");
  const [selectedCrop, setSelectedCrop] = useState("All Crops");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [notice, setNotice] = useState("");

  // Fetch only the authenticated user's prediction history.
  const fetchHistory = async () => {
    try {
      setLoading(true);
      setNotice("");

      const response = await fetch(HISTORY_API_URL, {
        method: "GET",
        credentials: "include",
      });
      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          setRecords([]);
          setSelectedRecord(null);
          setNotice("Please log in to view your prediction history.");
          return;
        }
        throw new Error(data.message || "Unable to load prediction history.");
      }

      const savedRecords = Array.isArray(data.records)
        ? data.records.map((record) => ({
            ...record,
            id: record._id,
            type: "Disease Detection",
            status: "Saved",
          }))
        : [];

      setRecords(savedRecords);
    } catch (error) {
      console.error("Prediction history fetch error:", error);
      setNotice(error.message || "Unable to load prediction history.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const filteredRecords = useMemo(() => {
    const query = search.trim().toLowerCase();

    return records.filter((record) => {
      const searchableText = [
        record.crop,
        record.disease,
        record.type,
        record.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const matchesSearch = !query || searchableText.includes(query);
      const matchesType =
        analysisType === "All Types" || record.type === analysisType;
      const matchesCrop =
        selectedCrop === "All Crops" || record.crop === selectedCrop;

      const recordDate = record.createdAt ? new Date(record.createdAt) : null;
      const matchesStart =
        !startDate ||
        (recordDate && recordDate >= new Date(`${startDate}T00:00:00`));
      const matchesEnd =
        !endDate ||
        (recordDate && recordDate <= new Date(`${endDate}T23:59:59.999`));

      const matchesCategory =
        activeCategory === "All" ||
        activeCategory === "Export Reports" ||
        activeCategory === "Delete Records" ||
        activeCategory === "FAQs" ||
        record.type === activeCategory;

      return (
        matchesSearch &&
        matchesType &&
        matchesCrop &&
        matchesStart &&
        matchesEnd &&
        matchesCategory
      );
    });
  }, [
    records,
    search,
    analysisType,
    selectedCrop,
    startDate,
    endDate,
    activeCategory,
  ]);

  const handleExport = () => {
    if (!filteredRecords.length) {
      setNotice("No saved records are available to export.");
      return;
    }

    const headers = [
      "Crop",
      "Disease or Result",
      "Confidence (%)",
      "Probabilities",
      "Date",
    ];

    const rows = filteredRecords.map((record) => [
      record.crop,
      record.disease,
      record.confidence,
      Array.isArray(record.probabilities)
        ? record.probabilities
            .map((item) => `${item.name}: ${item.value}%`)
            .join("; ")
        : "",
      record.createdAt ? new Date(record.createdAt).toLocaleString() : "",
    ]);

    const csv = [headers, ...rows]
      .map((row) =>
        row
          .map((value) => `"${String(value ?? "").replace(/"/g, '""')}"`)
          .join(",")
      )
      .join("\r\n");

    const blob = new Blob(["\uFEFF" + csv], {
      type: "text/csv;charset=utf-8;",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "kisanvision-prediction-history.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    setNotice("Your prediction history was exported successfully.");
  };

  const handleNavigation = (value) => {
    setActiveCategory(value);
    setSelectedRecord(null);
    setNotice("");

    if (value === "Export Reports") {
      handleExport();
    } else if (value === "Delete Records") {
      setNotice(
        records.length
          ? "Select a record to delete it, or clear all your saved records."
          : "There are no saved records to delete."
      );
    } else if (value === "FAQs") {
      setNotice(
        "Prediction history contains saved disease detection results for your account."
      );
    }
  };

  const clearFilters = () => {
    setSearch("");
    setAnalysisType("All Types");
    setSelectedCrop("All Crops");
    setStartDate("");
    setEndDate("");
    setActiveCategory("All");
    setNotice("");
  };

  const handleDeleteRecord = async () => {
    if (!selectedRecord?._id || deleting) return;

    const confirmed = window.confirm(
      "Are you sure you want to delete this prediction record?"
    );
    if (!confirmed) return;

    try {
      setDeleting(true);
      setNotice("");

      const response = await fetch(
        `${HISTORY_API_URL}/${selectedRecord._id}`,
        {
          method: "DELETE",
          credentials: "include",
        }
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Unable to delete this record.");
      }

      setRecords((previous) =>
        previous.filter((record) => record._id !== selectedRecord._id)
      );
      setSelectedRecord(null);
      setNotice("Prediction record deleted successfully.");
    } catch (error) {
      console.error("Delete prediction error:", error);
      setNotice(error.message || "Unable to delete prediction.");
    } finally {
      setDeleting(false);
    }
  };

  const handleClearHistory = async () => {
    if (!records.length || deleting) {
      setNotice("There are no saved records to delete.");
      return;
    }

    const confirmed = window.confirm(
      "Are you sure you want to delete all your prediction history? This cannot be undone."
    );
    if (!confirmed) return;

    try {
      setDeleting(true);
      setNotice("");

      const response = await fetch(HISTORY_API_URL, {
        method: "DELETE",
        credentials: "include",
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Unable to clear prediction history.");
      }

      setRecords([]);
      setSelectedRecord(null);
      setNotice("Your prediction history was cleared successfully.");
    } catch (error) {
      console.error("Clear prediction history error:", error);
      setNotice(error.message || "Unable to clear prediction history.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="ph-page">
      <aside className="ph-sidebar">
        <div className="ph-sidebar-heading">
          <span className="ph-sidebar-logo">
            <FaHistory />
          </span>
          <div>
            <h2>Prediction History</h2>
            <p>Review your past analyses</p>
          </div>
        </div>

        <nav className="ph-sidebar-nav" aria-label="History navigation">
          {historyNavigation.map(({ label, icon: Icon, value }) => (
            <button
              type="button"
              key={value}
              className={
                activeCategory === value
                  ? "ph-side-link active"
                  : "ph-side-link"
              }
              onClick={() => handleNavigation(value)}
            >
              <Icon />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="ph-sidebar-note">
          <FaSeedling />
          <h3>Your analyses, in one place</h3>
          <p>Your saved prediction results are securely linked to your account.</p>
        </div>
      </aside>

      <section className="ph-content">
        <header className="ph-page-heading">
          <div className="ph-heading-icon">
            <FaHistory />
          </div>
          <div className="ph-heading-copy">
            <span className="ph-eyebrow">KISANVISION AI / WORKSPACE</span>
            <h1>Prediction History</h1>
            <p>View and manage your past analyses and results.</p>
          </div>
        </header>

        <section className="ph-filter-panel">
          <div className="ph-field ph-search-field">
            <label htmlFor="ph-search">Search</label>
            <div className="ph-input-wrap">
              <FaSearch />
              <input
                id="ph-search"
                type="search"
                placeholder="Search by crop, disease or result..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </div>

          <div className="ph-field">
            <label htmlFor="ph-type">Analysis Type</label>
            <div className="ph-select-wrap">
              <select
                id="ph-type"
                value={analysisType}
                onChange={(event) => setAnalysisType(event.target.value)}
              >
                <option>All Types</option>
                <option>Disease Detection</option>
              </select>
              <FaChevronDown />
            </div>
          </div>

          <div className="ph-field">
            <label htmlFor="ph-crop">Crop</label>
            <div className="ph-select-wrap">
              <select
                id="ph-crop"
                value={selectedCrop}
                onChange={(event) => setSelectedCrop(event.target.value)}
              >
                <option>All Crops</option>
                {["Coffee", "Arecanut", "Cardamom", "Ginger"].map((crop) => (
                  <option key={crop}>{crop}</option>
                ))}
              </select>
              <FaChevronDown />
            </div>
          </div>

          <div className="ph-field ph-date-field">
            <label htmlFor="ph-start-date">Date Range — From</label>
            <div className="ph-input-wrap">
              <FaCalendarAlt />
              <input
                id="ph-start-date"
                type="date"
                value={startDate}
                max={endDate || undefined}
                onChange={(event) => setStartDate(event.target.value)}
              />
            </div>
          </div>

          <div className="ph-field ph-date-field">
            <label htmlFor="ph-end-date">To</label>
            <div className="ph-input-wrap">
              <FaCalendarAlt />
              <input
                id="ph-end-date"
                type="date"
                value={endDate}
                min={startDate || undefined}
                onChange={(event) => setEndDate(event.target.value)}
              />
            </div>
          </div>

          <button
            type="button"
            className="ph-filter-button"
            onClick={() => setNotice("Filters applied to your saved records.")}
          >
            <FaFilter /> Filter
          </button>

          <button
            type="button"
            className="ph-clear-button"
            onClick={clearFilters}
          >
            Clear
          </button>
        </section>

        {notice && (
          <div className="ph-notice" role="status">
            <FaInfoCircle />
            <span>{notice}</span>
            <button
              type="button"
              aria-label="Dismiss message"
              onClick={() => setNotice("")}
            >
              <FaTimes />
            </button>
          </div>
        )}

        {activeCategory === "FAQs" ? (
          <section className="ph-empty-panel">
            <FaQuestionCircle className="ph-empty-icon" />
            <h2>Prediction History FAQs</h2>
            <p>
              Your disease detection predictions are saved to your account.
              Only you can view and manage your saved records.
            </p>
            <button
              type="button"
              className="ph-secondary-button"
              onClick={() => handleNavigation("All")}
            >
              Back to all analyses
            </button>
          </section>
        ) : (
          <>
            <div className="ph-summary-row">
              <div>
                <h2>
                  <FaHistory /> Analysis History
                </h2>
                <p>
                  {filteredRecords.length} saved{" "}
                  {filteredRecords.length === 1 ? "record" : "records"}
                </p>
              </div>

              <div>
                <button
                  type="button"
                  className="ph-export-button"
                  onClick={handleExport}
                  disabled={!filteredRecords.length || loading}
                >
                  <FaDownload /> Export All
                </button>
                <button
                  type="button"
                  className="ph-delete-button"
                  onClick={handleClearHistory}
                  disabled={!records.length || deleting || loading}
                >
                  <FaTrashAlt /> Clear All
                </button>
              </div>
            </div>

            <div className="ph-main-grid">
              <section className="ph-table-panel">
                <div className="ph-table-topline">
                  <h3>
                    {activeCategory === "All" ? "All Analyses" : activeCategory}
                  </h3>
                  <span>{filteredRecords.length} results</span>
                </div>

                {loading ? (
                  <div className="ph-empty-state">
                    <h3>Loading prediction history...</h3>
                    <p>Please wait while your saved records are retrieved.</p>
                  </div>
                ) : filteredRecords.length === 0 ? (
                  <div className="ph-empty-state">
                    <div className="ph-empty-illustration">
                      <FaClipboardList />
                    </div>
                    <h3>No saved analyses yet</h3>
                    <p>
                      When you complete a disease detection prediction, its
                      crop, result, confidence and date will appear here.
                    </p>
                    {(search ||
                      analysisType !== "All Types" ||
                      selectedCrop !== "All Crops" ||
                      startDate ||
                      endDate ||
                      activeCategory !== "All") && (
                      <button
                        type="button"
                        className="ph-secondary-button"
                        onClick={clearFilters}
                      >
                        Clear filters
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="ph-table-scroll">
                    <table className="ph-table">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Crop</th>
                          <th>Disease / Result</th>
                          <th>Type</th>
                          <th>Date &amp; Time</th>
                          <th>Confidence</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredRecords.map((record, index) => (
                          <tr key={record._id}>
                            <td>{index + 1}</td>
                            <td>{record.crop}</td>
                            <td>{record.disease || "Not provided"}</td>
                            <td>{record.type}</td>
                            <td>
                              {record.createdAt
                                ? new Date(record.createdAt).toLocaleString()
                                : "Date unavailable"}
                            </td>
                            <td>{Number(record.confidence).toFixed(2)}%</td>
                            <td>
                              <button
                                type="button"
                                className="ph-view-button"
                                onClick={() => setSelectedRecord(record)}
                              >
                                <FaEye /> View
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>

              <aside className="ph-details-panel">
                <div className="ph-details-heading">
                  <h2>
                    <FaEye /> Analysis Details
                  </h2>
                </div>

                {selectedRecord ? (
                  <div className="ph-record-details">
                    <h3>{selectedRecord.crop}</h3>
                    <p>{selectedRecord.disease || "Result unavailable"}</p>
                    <dl>
                      <dt>Analysis type</dt>
                      <dd>{selectedRecord.type}</dd>
                      <dt>Confidence</dt>
                      <dd>{Number(selectedRecord.confidence).toFixed(2)}%</dd>
                      <dt>Status</dt>
                      <dd>{selectedRecord.status || "Saved"}</dd>
                      <dt>Date</dt>
                      <dd>
                        {selectedRecord.createdAt
                          ? new Date(selectedRecord.createdAt).toLocaleString()
                          : "Unavailable"}
                      </dd>
                    </dl>

                    {Array.isArray(selectedRecord.probabilities) &&
                      selectedRecord.probabilities.length > 0 && (
                        <div className="ph-probabilities">
                          <h4>Prediction Probabilities</h4>
                          {selectedRecord.probabilities.map((item, index) => (
                            <div key={`${item.name}-${index}`}>
                              <span>
                                {item.name}: {item.value}%
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                  </div>
                ) : (
                  <div className="ph-details-empty">
                    <FaEye />
                    <h3>Select a record</h3>
                    <p>
                      Select a saved analysis from the history table to see
                      its details here.
                    </p>
                  </div>
                )}

                <div className="ph-detail-actions">
                  <h3>Actions</h3>
                  <p>Manage the selected saved prediction.</p>
                  <button
                    type="button"
                    className="ph-delete-button"
                    disabled={!selectedRecord || deleting}
                    onClick={handleDeleteRecord}
                  >
                    <FaTrashAlt />
                    {deleting ? "Deleting..." : "Delete Record"}
                  </button>
                </div>
              </aside>
            </div>
          </>
        )}
      </section>
    </div>
  );
}

export default PredictionHistory;
