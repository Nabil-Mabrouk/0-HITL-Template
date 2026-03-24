import { ComposableMap, Geographies, Geography, Marker } from "react-simple-maps";

import { scaleLinear } from "d3-scale";
import { useState } from "react";

const GEO_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface CountryData {
  country_code: string;
  country_name: string;
  visits:       number;
}

interface CityData {
  city:         string;
  country_code: string;
  latitude:     number;
  longitude:    number;
  visits:       number;
}

interface Props {
  countries: CountryData[];
  cities:    CityData[];
}

// Mapping ISO2 -> ISO numeric pour react-simple-maps
const ISO2_TO_NUM: Record<string, string> = {
  FR: "250", US: "840", GB: "826", DE: "276", JP: "392",
  CN: "156", BR: "076", IN: "356", CA: "124", AU: "036",
  ES: "724", IT: "380", RU: "643", KR: "410", MX: "484",
  // Ajouter selon les besoins
};

export default function WorldMap({ countries, cities }: Props) {
  const [tooltip, setTooltip] = useState<string | null>(null);
  const [mode, setMode]       = useState<"countries" | "cities">("countries");

  const maxVisits = Math.max(...countries.map(c => c.visits), 1);
  const colorScale = scaleLinear<string>()
    .domain([0, maxVisits])
    .range(["#1a1a2e", "#6366f1"]);

  const countryMap = Object.fromEntries(
    countries.map(c => [ISO2_TO_NUM[c.country_code] ?? c.country_code, c])
  );

  const maxCityVisits = Math.max(...cities.map(c => c.visits), 1);

  return (
    <div className="relative">
      {/* Toggle mode */}
      <div className="flex gap-2 mb-4">
        {(["countries", "cities"] as const).map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`text-xs px-3 py-1.5 rounded-full border transition
              ${mode === m
                ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                : "border-white/10 text-white/40 hover:text-white"
              }`}
          >
            {m === "countries" ? "Par pays" : "Par ville"}
          </button>
        ))}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div className="absolute top-0 left-1/2 -translate-x-1/2
                        bg-zinc-900 border border-white/10 rounded-lg
                        px-3 py-1.5 text-xs text-white z-10 pointer-events-none">
          {tooltip}
        </div>
      )}

      <ComposableMap
        projection="geoMercator"
        style={{ width: "100%", height: "auto" }}
      >
        <Geographies geography={GEO_URL}>
          {({ geographies }: { geographies: any[] }) =>
            geographies.map((geo: any) => {
              const data = countryMap[geo.id];
              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill={data ? colorScale(data.visits) : "#1a1a2e"}
                  stroke="#2a2a3e"
                  strokeWidth={0.5}
                  onMouseEnter={() => {
                    if (data) {
                      setTooltip(
                        `${data.country_name} — ${data.visits} visite${data.visits > 1 ? "s" : ""}`
                      );
                    }
                  }}
                  onMouseLeave={() => setTooltip(null)}
                  style={{
                    default:  { outline: "none" },
                    hover:    { outline: "none", fill: "#818cf8" },
                    pressed:  { outline: "none" },
                  }}
                />
              );
            })
          }
        </Geographies>

        {/* Points villes */}
        {mode === "cities" && cities.map((city, i) => {
          const r = 2 + (city.visits / maxCityVisits) * 12;
          return (
            <Marker
              key={i}
              coordinates={[city.longitude, city.latitude]}
              onMouseEnter={() =>
                setTooltip(`${city.city} — ${city.visits} visite${city.visits > 1 ? "s" : ""}`)
              }
              onMouseLeave={() => setTooltip(null)}
            >
              <circle
                r={r}
                fill="#f59e0b"
                fillOpacity={0.7}
                stroke="#f59e0b"
                strokeWidth={0.5}
              />
            </Marker>
          );
        })}
      </ComposableMap>

      {/* Légende choroplèthe */}
      {mode === "countries" && (
        <div className="flex items-center gap-2 mt-2 text-xs text-white/40">
          <span>0</span>
          <div className="flex-1 h-2 rounded"
               style={{ background: "linear-gradient(to right, #1a1a2e, #6366f1)" }} />
          <span>{maxVisits}</span>
        </div>
      )}
    </div>
  );
}