
import { useState } from "react";
import {
  FaCloudSun,
  FaSeedling,
  FaMapMarkerAlt,
  FaCloud,
  FaCloudRain,
  FaSun,
  FaWind,
  FaTint,
  FaThermometerHalf,
  FaLeaf,
  FaWater,
  FaSearch,
  FaQuestionCircle,
  FaInfoCircle,
  FaChevronDown,
  FaBars,
  FaTimes,
  FaCalendarAlt,
  FaLocationArrow,
  FaSpinner,
  FaUmbrella,
  FaChartLine,
} from "react-icons/fa";
import "./WeatherRecommendation.css";

// Weather and location data are fetched directly from these public services.
// This component does not require a Render backend URL.
const OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast";
const OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search";
const OPEN_STREET_MAP_SEARCH_URL = "https://nominatim.openstreetmap.org/search";
const OPEN_STREET_MAP_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse";

const STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
  "Chhattisgarh", "Goa", "Gujarat", "Haryana",
  "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
  "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
  "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan",
  "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
  "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Andaman and Nicobar Islands", "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi", "Jammu and Kashmir", "Ladakh",
  "Lakshadweep", "Puducherry",
];

const CROPS = [
  {
    name: "Coffee",
    description:
      "Review local temperature and rainfall patterns before planning coffee cultivation.",
    icon: "☕",
  },
  {
    name: "Arecanut",
    description:
      "Consider rainfall, humidity and local water conditions for arecanut cultivation.",
    icon: "🌴",
  },
  {
    name: "Cardamom",
    description:
      "Check local humidity, rainfall and growing-region conditions for cardamom.",
    icon: "🌿",
  },
  {
    name: "Ginger",
    description:
      "Monitor rainfall and drainage conditions when planning ginger cultivation.",
    icon: "🫚",
  },
];

const FAQS = [
  {
    q: "How does weather-based crop guidance work?",
    a: "The dashboard examines current weather and the upcoming forecast. It provides preliminary weather guidance for Coffee, Arecanut, Cardamom and Ginger. Weather alone cannot establish whether a crop is suitable for a farm.",
  },
  {
    q: "Where does the weather data come from?",
    a: "Weather information is retrieved from Open-Meteo. Location suggestions use OpenStreetMap. An internet connection is required.",
  },
  {
    q: "Can I use my current location?",
    a: "Yes. Select Use Live Location and allow your browser to access your location. The dashboard will retrieve weather for those coordinates.",
  },
  {
    q: "Can I select a village manually?",
    a: "Yes. Select a state and enter the district, taluk and village or nearby place. Location suggestions are provided using OpenStreetMap data.",
  },
  {
    q: "Are crop recommendations guaranteed?",
    a: "No. Short-term weather cannot guarantee crop suitability. Soil, elevation, crop variety, growing season, irrigation and local agricultural guidance must also be considered.",
  },
];

const weatherCode = (code) => {
  if (code === 0) return { label: "Clear sky", icon: FaSun };
  if ([1, 2].includes(code))
    return { label: "Partly cloudy", icon: FaCloudSun };
  if (code === 3) return { label: "Overcast", icon: FaCloud };
  if ([45, 48].includes(code))
    return { label: "Fog", icon: FaCloud };
  if ([51, 53, 55, 56, 57].includes(code))
    return { label: "Drizzle", icon: FaCloudRain };
  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(code))
    return { label: "Rain", icon: FaCloudRain };
  if ([71, 73, 75, 77, 85, 86].includes(code))
    return { label: "Snow", icon: FaCloud };
  if ([95, 96, 99].includes(code))
    return { label: "Thunderstorm", icon: FaCloudRain };

  return { label: "Weather unavailable", icon: FaCloudSun };
};

const navItems = [
  { id: "overview", label: "Crop Recommendation", icon: FaSeedling },
  { id: "current-weather", label: "Current Weather", icon: FaCloudSun },
  { id: "forecast", label: "Forecast & Analysis", icon: FaCalendarAlt },
  { id: "crop-requirements", label: "Crop Recommendations", icon: FaLeaf },
  { id: "insights", label: "Key Weather Insights", icon: FaChartLine },
  { id: "faqs", label: "FAQs", icon: FaQuestionCircle },
];

const formatDate = (date, options) =>
  new Date(`${date}T12:00:00`).toLocaleDateString("en-IN", options);

export default function WeatherRecommendation() {
  const [state, setState] = useState("Karnataka");
  const [district, setDistrict] = useState("");
  const [taluk, setTaluk] = useState("");
  const [village, setVillage] = useState("");

  const [weather, setWeather] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [locationName, setLocationName] = useState("");
  const [coordinates, setCoordinates] = useState(null);

  const [loading, setLoading] = useState(false);
  const [locationLoading, setLocationLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const [activeSection, setActiveSection] = useState("overview");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [expandedFaq, setExpandedFaq] = useState(0);

  const [suggestions, setSuggestions] = useState({
    district: [],
    taluk: [],
    village: [],
  });

  const [suggestionLoading, setSuggestionLoading] = useState("");

  const navigateTo = (id) => {
    setActiveSection(id);
    setMobileMenuOpen(false);

    document.getElementById(`wr-${id}`)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  // Get location suggestions from OpenStreetMap.
  const getSuggestions = async (level, value) => {
    if (!value.trim() || !state) {
      setSuggestions((previous) => ({
        ...previous,
        [level]: [],
      }));
      return;
    }

    setSuggestionLoading(level);

    try {
      const query = [value, state, "India"].filter(Boolean).join(", ");

      const response = await fetch(
        `${OPEN_STREET_MAP_SEARCH_URL}?format=jsonv2&addressdetails=1&limit=8&q=${encodeURIComponent(query)}`
      );

      if (!response.ok) throw new Error("Location suggestions unavailable.");

      const results = await response.json();

      const names = results
        .map((item) => {
          const address = item.address || {};

          if (level === "district") {
            return (
              address.county ||
              address.state_district ||
              address.city_district ||
              address.city ||
              address.town
            );
          }

          if (level === "taluk") {
            return (
              address.suburb ||
              address.city_district ||
              address.county ||
              address.town ||
              address.village
            );
          }

          return (
            address.village ||
            address.hamlet ||
            address.suburb ||
            address.town ||
            address.city
          );
        })
        .filter(Boolean);

      setSuggestions((previous) => ({
        ...previous,
        [level]: [...new Set(names)],
      }));
    } catch {
      setSuggestions((previous) => ({
        ...previous,
        [level]: [],
      }));
    } finally {
      setSuggestionLoading("");
    }
  };

  // Get weather using latitude and longitude.
  const loadWeather = async (latitude, longitude, name) => {
    setLoading(true);
    setError("");
    setWeather(null);
    setForecast([]);
    setSearched(false);

    try {
      const params = new URLSearchParams({
        latitude: String(latitude),
        longitude: String(longitude),
        current:
          "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        daily:
          "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
        timezone: "auto",
        forecast_days: "5",
      });

      const response = await fetch(
        `${OPEN_METEO_FORECAST_URL}?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error("Weather service is unavailable. Please try again.");
      }

      const data = await response.json();

      if (!data.current || !data.daily) {
        throw new Error("Complete weather information was not returned.");
      }

      setWeather(data.current);
      setLocationName(name);
      setCoordinates({ latitude, longitude });

      setForecast(
        data.daily.time.map((date, index) => ({
          date,
          code: data.daily.weather_code?.[index],
          max: data.daily.temperature_2m_max?.[index],
          min: data.daily.temperature_2m_min?.[index],
          rainChance:
            data.daily.precipitation_probability_max?.[index],
          rainfall: data.daily.precipitation_sum?.[index],
        }))
      );

      setSearched(true);
    } catch (err) {
      setError(err.message || "Unable to retrieve weather information.");
    } finally {
      setLoading(false);
    }
  };

  // Search a manually entered location.
  const handleLocationSearch = async (event) => {
    event.preventDefault();
    setError("");

    const placeQuery = village.trim() || taluk.trim() || district.trim();

    if (!state || (!district && !taluk && !village)) {
      setError("Select a state and enter a district, taluk or village.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `${OPEN_METEO_GEOCODING_URL}?name=${encodeURIComponent(placeQuery)}&count=10&language=en&format=json`
      );

      if (!response.ok) {
        throw new Error("Could not search for this location.");
      }

      const data = await response.json();

      const matches = (data.results || []).filter(
        (item) => item.country_code?.toLowerCase() === "in"
      );

      const place =
        matches.find(
          (item) =>
            !item.admin1 ||
            item.admin1.toLowerCase() === state.toLowerCase()
        ) || matches[0];

      if (!place) {
        throw new Error(
          "Location not found. Try entering a nearby town or village name."
        );
      }

      const name = [
        village || place.name,
        taluk,
        district || place.admin2,
        state,
        "India",
      ]
        .filter(Boolean)
        .join(", ");

      await loadWeather(place.latitude, place.longitude, name);
    } catch (err) {
      setError(err.message || "Unable to find this location.");
      setLoading(false);
    }
  };

  // Browser live location.
  const useLiveLocation = () => {
    setError("");

    if (!navigator.geolocation) {
      setError("Your browser does not support live location.");
      return;
    }

    setLocationLoading(true);

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude, longitude } = position.coords;

        try {
          const response = await fetch(
            `${OPEN_STREET_MAP_REVERSE_URL}?format=jsonv2&lat=${latitude}&lon=${longitude}&zoom=10&addressdetails=1`
          );

          const data = await response.json();
          const address = data.address || {};

          const foundState = address.state || "";
          const foundDistrict =
            address.state_district ||
            address.county ||
            address.city_district ||
            address.city ||
            "";
          const foundTaluk = address.suburb || address.town || "";
          const foundVillage =
            address.village ||
            address.hamlet ||
            address.town ||
            address.city ||
            "";

          if (foundState) {
            setState(foundState);
          }

          setDistrict(foundDistrict);
          setTaluk(foundTaluk);
          setVillage(foundVillage);

          const name =
            data.display_name ||
            `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;

          await loadWeather(latitude, longitude, name);
        } catch {
          await loadWeather(
            latitude,
            longitude,
            `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`
          );
        } finally {
          setLocationLoading(false);
        }
      },
      (geoError) => {
        const messages = {
          1: "Location permission was denied. Allow location access in your browser.",
          2: "Your current location could not be determined.",
          3: "Location request timed out. Please try again.",
        };

        setError(messages[geoError.code] || "Unable to access live location.");
        setLocationLoading(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 300000,
      }
    );
  };

  const currentCondition = weather
    ? weatherCode(weather.weather_code)
    : null;
  const CurrentWeatherIcon = currentCondition?.icon;

  const tomorrow = forecast[1];
  const dayAfterTomorrow = forecast[2];

  // Weather observations used to create general insights.
  const getInsights = () => {
    if (!weather || forecast.length === 0) return [];

    const upcomingDays = forecast.slice(1, 5);
    const totalRain = upcomingDays.reduce(
      (sum, day) => sum + (Number(day.rainfall) || 0),
      0
    );

    const averageTemperature =
      upcomingDays.reduce(
        (sum, day) => sum + (Number(day.max) || 0),
        0
      ) / Math.max(upcomingDays.length, 1);

    const insights = [];

    if (totalRain >= 20) {
      insights.push({
        icon: FaUmbrella,
        text: `Rainfall of approximately ${totalRain.toFixed(1)} mm is forecast over the next four days.`,
      });
    } else {
      insights.push({
        icon: FaCloudSun,
        text: "Limited rainfall is currently forecast over the next four days.",
      });
    }

    if (averageTemperature >= 32) {
      insights.push({
        icon: FaThermometerHalf,
        text: "Forecast daytime temperatures are relatively high. Monitor heat and water stress.",
      });
    } else if (averageTemperature <= 20) {
      insights.push({
        icon: FaThermometerHalf,
        text: "Forecast daytime temperatures are relatively cool.",
      });
    } else {
      insights.push({
        icon: FaThermometerHalf,
        text: "Forecast daytime temperatures are moderate.",
      });
    }

    if (weather.relative_humidity_2m >= 80) {
      insights.push({
        icon: FaTint,
        text: "Current humidity is high. Monitor crops for moisture-related disease risks.",
      });
    } else {
      insights.push({
        icon: FaTint,
        text: "Current relative humidity is " +
          `${weather.relative_humidity_2m}%.`,
      });
    }

    const rainyDays = upcomingDays.filter(
      (day) => Number(day.rainChance) >= 60
    ).length;

    insights.push({
      icon: FaCloudRain,
      text: rainyDays
        ? `${rainyDays} upcoming day(s) have a rain probability of 60% or more.`
        : "No upcoming day currently has a rain probability of 60% or more.",
    });

    return insights;
  };

  const insights = getInsights();

  return (
    <div className="wr-page">
      <header className="wr-heading">
        <button
          type="button"
          className="wr-mobile-menu"
          aria-label="Toggle dashboard navigation"
          aria-expanded={mobileMenuOpen}
          onClick={() => setMobileMenuOpen((value) => !value)}
        >
          {mobileMenuOpen ? <FaTimes /> : <FaBars />}
        </button>

        <div className="wr-heading-icon">
          <FaCloudSun />
        </div>

        <div className="wr-heading-copy">
          <span className="wr-eyebrow">
            KISANVISION AI / SMART FARMING
          </span>
          <h1>Weather-Aware Crop Recommendation</h1>
          <p>
            Explore local weather conditions and weather-based crop guidance.
          </p>
        </div>

        <span className="wr-live-status">
          <span />
          LIVE WEATHER LOOKUP
        </span>
      </header>

      <div className="wr-layout">
        <aside
          className={`wr-sidebar ${mobileMenuOpen ? "wr-sidebar-open" : ""}`}
          aria-label="Weather dashboard navigation"
        >
          <div className="wr-sidebar-brand">
            <span><FaSeedling /></span>
            <div>
              <strong>Farm Dashboard</strong>
              <small>Weather & crop planning</small>
            </div>
          </div>

          <nav className="wr-nav">
            {navItems.map(({ id, label, icon: Icon }) => (
              <button
                type="button"
                key={id}
                className={activeSection === id ? "active" : ""}
                onClick={() => navigateTo(id)}
              >
                <Icon />
                <span>{label}</span>
              </button>
            ))}
          </nav>

          <div className="wr-sidebar-photo">
            <strong>Right Crop<br />Better Yield</strong>
            <span>Sustainable Tomorrow</span>
          </div>
        </aside>

        {mobileMenuOpen && (
          <button
            type="button"
            className="wr-backdrop"
            aria-label="Close dashboard navigation"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        <main className="wr-main">
          {/* LOCATION */}
          <section className="wr-card wr-location-card" id="wr-overview">
            <div className="wr-section-heading">
              <div>
                <span className="wr-kicker">YOUR LOCATION</span>
                <h2><FaMapMarkerAlt /> Select Your Location</h2>
                <p>
                  Choose your location manually or use your current location.
                </p>
              </div>
            </div>

            <form
              className="wr-location-form"
              onSubmit={handleLocationSearch}
            >
              <label className="wr-field">
                <span>State / Union Territory</span>
                <select
                  value={state}
                  onChange={(event) => {
                    setState(event.target.value);
                    setDistrict("");
                    setTaluk("");
                    setVillage("");
                    setSuggestions({
                      district: [],
                      taluk: [],
                      village: [],
                    });
                  }}
                  required
                >
                  <option value="">Select State / UT</option>
                  {STATES.map((item) => (
                    <option value={item} key={item}>{item}</option>
                  ))}
                </select>
              </label>

              <label className="wr-field">
                <span>District</span>
                <input
                  list="wr-district-options"
                  value={district}
                  onChange={(event) => {
                    setDistrict(event.target.value);
                    setTaluk("");
                    setVillage("");
                  }}
                  onBlur={() => getSuggestions("district", district)}
                  onKeyUp={() => getSuggestions("district", district)}
                  placeholder="Enter or select district"
                  autoComplete="off"
                />
                <datalist id="wr-district-options">
                  {suggestions.district.map((item) => (
                    <option value={item} key={item} />
                  ))}
                </datalist>
                {suggestionLoading === "district" && (
                  <small>Finding district suggestions...</small>
                )}
              </label>

              <label className="wr-field">
                <span>Taluk / Sub-district</span>
                <input
                  list="wr-taluk-options"
                  value={taluk}
                  onChange={(event) => {
                    setTaluk(event.target.value);
                    setVillage("");
                  }}
                  onBlur={() => getSuggestions("taluk", taluk)}
                  onKeyUp={() => getSuggestions("taluk", taluk)}
                  placeholder="Enter or select taluk"
                  autoComplete="off"
                />
                <datalist id="wr-taluk-options">
                  {suggestions.taluk.map((item) => (
                    <option value={item} key={item} />
                  ))}
                </datalist>
                {suggestionLoading === "taluk" && (
                  <small>Finding taluk suggestions...</small>
                )}
              </label>

              <label className="wr-field">
                <span>Village / Current Place</span>
                <input
                  list="wr-village-options"
                  value={village}
                  onChange={(event) => setVillage(event.target.value)}
                  onBlur={() => getSuggestions("village", village)}
                  onKeyUp={() => getSuggestions("village", village)}
                  placeholder="Enter village or nearby place"
                  autoComplete="off"
                />
                <datalist id="wr-village-options">
                  {suggestions.village.map((item) => (
                    <option value={item} key={item} />
                  ))}
                </datalist>
                {suggestionLoading === "village" && (
                  <small>Finding village suggestions...</small>
                )}
              </label>

              <button
                type="submit"
                className="wr-primary-button"
                disabled={loading || locationLoading}
              >
                {loading ? <FaSpinner className="wr-spin" /> : <FaSearch />}
                {loading ? "Fetching weather..." : "Get Weather Data"}
              </button>

              <button
                type="button"
                className="wr-primary-button wr-location-button"
                onClick={useLiveLocation}
                disabled={loading || locationLoading}
              >
                {locationLoading ? (
                  <FaSpinner className="wr-spin" />
                ) : (
                  <FaLocationArrow />
                )}
                {locationLoading ? "Detecting location..." : "Use Live Location"}
              </button>
            </form>

            {error && (
              <div className="wr-error" role="alert">
                <FaInfoCircle />
                <span>{error}</span>
              </div>
            )}

            <p className="wr-data-note">
              <FaInfoCircle />
              Location suggestions are provided by OpenStreetMap.
              Weather data is retrieved from Open-Meteo.
            </p>
          </section>

          {/* CURRENT WEATHER */}
          <section className="wr-section" id="wr-current-weather">
            <div className="wr-section-heading">
              <div>
                <span className="wr-kicker">LOCAL CONDITIONS</span>
                <h2><FaCloudSun /> Current Weather</h2>
                <p>
                  {searched
                    ? locationName
                    : "Select a location to view current weather."}
                </p>
              </div>
              {searched && (
                <span className="wr-data-badge">LIVE API DATA</span>
              )}
            </div>

            {!weather ? (
              <div className="wr-empty-weather">
                <FaCloudSun />
                <strong>Weather data not loaded</strong>
                <p>Choose your location to view live weather information.</p>
              </div>
            ) : (
              <div className="wr-weather-grid">
                <article className="wr-weather-main">
                  <div className="wr-weather-place">
                    <FaMapMarkerAlt /> {locationName}
                  </div>
                  <div className="wr-current-summary">
                    {CurrentWeatherIcon && <CurrentWeatherIcon />}
                    <div>
                      <strong>
                        {Math.round(weather.temperature_2m)}°C
                      </strong>
                      <span>{currentCondition.label}</span>
                    </div>
                  </div>
                  <p>
                    Feels like{" "}
                    {Math.round(weather.apparent_temperature)}°C
                  </p>
                </article>

                <article className="wr-metric-card">
                  <FaTint />
                  <span>Humidity</span>
                  <strong>{weather.relative_humidity_2m}%</strong>
                </article>

                <article className="wr-metric-card">
                  <FaWind />
                  <span>Wind Speed</span>
                  <strong>{weather.wind_speed_10m} km/h</strong>
                </article>

                <article className="wr-metric-card">
                  <FaCloudRain />
                  <span>Rainfall</span>
                  <strong>{weather.precipitation} mm</strong>
                </article>
              </div>
            )}
          </section>

          {/* FORECAST */}
          <section className="wr-card" id="wr-forecast">
            <div className="wr-section-heading">
              <div>
                <span className="wr-kicker">UPCOMING CONDITIONS</span>
                <h2><FaCalendarAlt /> 5-Day Weather Forecast</h2>
                <p>Temperature, rainfall and rain probability.</p>
              </div>
            </div>

            {forecast.length === 0 ? (
              <div className="wr-inline-empty">
                <FaCalendarAlt />
                <span>Search for a location to load the forecast.</span>
              </div>
            ) : (
              <>
                <div className="wr-forecast-grid">
                  {forecast.map((day, index) => {
                    const condition = weatherCode(day.code);
                    const WeatherIcon = condition.icon;

                    return (
                      <article className="wr-forecast-day" key={day.date}>
                        <strong>
                          {index === 0
                            ? "Today"
                            : formatDate(day.date, { weekday: "short" })}
                        </strong>

                        <span className="wr-forecast-date">
                          {formatDate(day.date, {
                            day: "numeric",
                            month: "short",
                          })}
                        </span>

                        <WeatherIcon />

                        <span className="wr-forecast-condition">
                          {condition.label}
                        </span>

                        <strong className="wr-forecast-temperatures">
                          {day.max == null ? "—" : `${Math.round(day.max)}°`}
                          {" / "}
                          {day.min == null ? "—" : `${Math.round(day.min)}°`}
                        </strong>

                        <span className="wr-forecast-detail">
                          <FaCloudRain />
                          {day.rainChance == null ? "—" : `${day.rainChance}%`}
                        </span>

                        <span className="wr-forecast-detail">
                          Rain: {day.rainfall == null ? "—" : `${day.rainfall} mm`}
                        </span>
                      </article>
                    );
                  })}
                </div>

                <div className="wr-requirement-grid">
                  <div>
                    <FaCalendarAlt />
                    <strong>Tomorrow</strong>
                    <span>
                      {tomorrow
                        ? `${Math.round(tomorrow.min)}°–${Math.round(tomorrow.max)}°C · Rain ${tomorrow.rainChance ?? "—"}%`
                        : "Forecast unavailable"}
                    </span>
                  </div>
                  <div>
                    <FaCalendarAlt />
                    <strong>Day After Tomorrow</strong>
                    <span>
                      {dayAfterTomorrow
                        ? `${Math.round(dayAfterTomorrow.min)}°–${Math.round(dayAfterTomorrow.max)}°C · Rain ${dayAfterTomorrow.rainChance ?? "—"}%`
                        : "Forecast unavailable"}
                    </span>
                  </div>
                </div>
              </>
            )}

            <p className="wr-footnote">
              Forecasts can change. Check local agricultural advisories
              before making farming decisions.
            </p>
          </section>

          {/* WEATHER INSIGHTS */}
          <section className="wr-card" id="wr-insights">
            <div className="wr-section-heading">
              <div>
                <span className="wr-kicker">WEATHER ANALYSIS</span>
                <h2><FaChartLine /> Key Weather Insights</h2>
                <p>Insights calculated from the retrieved weather forecast.</p>
              </div>
            </div>

            {insights.length === 0 ? (
              <div className="wr-inline-empty">
                <FaChartLine />
                <span>Weather insights will appear after a location search.</span>
              </div>
            ) : (
              <div className="wr-requirement-grid">
                {insights.map((item, index) => {
                  const InsightIcon = item.icon;

                  return (
                    <div key={index}>
                      <InsightIcon />
                      <span>{item.text}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* CROP RECOMMENDATIONS */}
          <section className="wr-card" id="wr-crop-requirements">
            <div className="wr-section-heading">
              <div>
                <span className="wr-kicker">CROP DECISION SUPPORT</span>
                <h2><FaSeedling /> Recommended Crops</h2>
                <p>
                  Weather-based information for your selected location.
                </p>
              </div>
            </div>

            {!searched ? (
              <div className="wr-inline-empty">
                <FaSeedling />
                <span>
                  Select a location and load weather to view crop guidance.
                </span>
              </div>
            ) : (
              <>
                <div className="wr-recommendation-pending">
                  <div className="wr-pending-icon">
                    <FaInfoCircle />
                  </div>
                  <div>
                    <strong>Preliminary weather guidance</strong>
                    <p>
                      These crops are shown for weather-context review.
                      This is not a validated crop suitability ranking.
                      Check soil, elevation, variety and local growing
                      conditions before choosing a crop.
                    </p>
                  </div>
                </div>

                <div className="wr-crop-grid">
                  {CROPS.map((crop) => (
                    <article className="wr-crop-card" key={crop.name}>
                      <div className="wr-crop-image-placeholder">
                        <span>{crop.icon}</span>
                      </div>
                      <h3>{crop.name}</h3>
                      <p>{crop.description}</p>
                      <span className="wr-crop-status">
                        Requires local verification
                      </span>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>

          {/* ADDITIONAL RECOMMENDATIONS */}
          <section className="wr-card">
            <div className="wr-section-heading">
              <div>
                <span className="wr-kicker">FARMER GUIDANCE</span>
                <h2><FaLeaf /> Additional Recommendations</h2>
              </div>
            </div>

            <div className="wr-requirement-grid">
              <div>
                <FaTint />
                <strong>Monitor rainfall</strong>
                <span>Check actual rainfall before irrigation decisions.</span>
              </div>
              <div>
                <FaWater />
                <strong>Check drainage</strong>
                <span>Prevent waterlogging during heavy rainfall.</span>
              </div>
              <div>
                <FaSeedling />
                <strong>Monitor crops</strong>
                <span>Inspect crops regularly for pests and diseases.</span>
              </div>
              <div>
                <FaCloudSun />
                <strong>Check forecasts</strong>
                <span>Review updated forecasts before field activities.</span>
              </div>
              <div>
                <FaInfoCircle />
                <strong>Local advice</strong>
                <span>Follow local agricultural department advisories.</span>
              </div>
            </div>
          </section>

          {/* FAQ */}
          <section className="wr-card" id="wr-faqs">
            <div className="wr-section-heading">
              <div>
                <span className="wr-kicker">HELP & GUIDANCE</span>
                <h2><FaQuestionCircle /> Frequently Asked Questions</h2>
              </div>
            </div>

            {FAQS.map((item, index) => (
              <div className="wr-faq" key={item.q}>
                <button
                  type="button"
                  aria-expanded={expandedFaq === index}
                  onClick={() =>
                    setExpandedFaq(expandedFaq === index ? -1 : index)
                  }
                >
                  <span>{item.q}</span>
                  <FaChevronDown
                    className={expandedFaq === index ? "rotated" : ""}
                  />
                </button>

                {expandedFaq === index && <p>{item.a}</p>}
              </div>
            ))}
          </section>

          <footer className="wr-footer">
            <span>KisanVision AI · BAI586 academic mini-project</span>
            <span>Weather: Open-Meteo · Location: OpenStreetMap</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
