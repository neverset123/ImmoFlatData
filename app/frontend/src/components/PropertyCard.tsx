import { useState } from "react";
import {
  ExternalLink,
  BedDouble,
  Ruler,
  MapPin,
  Building2,
  Calendar,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Listing } from "../types";

interface PropertyCardProps {
  listing: Listing;
}

function formatPrice(price: string): string {
  const num = parseInt(price, 10);
  if (isNaN(num)) return price;
  return num.toLocaleString("de-DE") + " \u20AC";
}

function Tags({ listing }: { listing: Listing }) {
  const tags: string[] = [];
  if (listing.balcony) tags.push("Balkon");
  if (listing.garden) tags.push("Garten");
  if (listing.cellar) tags.push("Keller");
  if (listing.lift) tags.push("Aufzug");
  if (listing.parking) tags.push("Stellplatz");
  if (tags.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {tags.map((tag) => (
        <span
          key={tag}
          className="px-2 py-0.5 text-xs rounded-full bg-white/15 backdrop-blur-sm"
        >
          {tag}
        </span>
      ))}
    </div>
  );
}

export function PropertyCard({ listing }: PropertyCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageFailed, setImageFailed] = useState(false);
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="h-screen w-full flex items-center justify-center snap-start relative">
      <div className="h-full w-full relative">
        {/* Background image */}
        {!imageFailed ? (
          <div className="absolute inset-0">
            <img
              loading="lazy"
              src={listing.imageUrl}
              alt={listing.title}
              className={`w-full h-full object-cover transition-opacity duration-300 ${
                imageLoaded ? "opacity-100" : "opacity-0"
              }`}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageFailed(true)}
            />
            {!imageLoaded && (
              <div className="absolute inset-0 bg-gray-900 animate-pulse" />
            )}
            <div className="absolute inset-0 bg-gradient-to-b from-black/10 via-transparent to-black/70" />
          </div>
        ) : (
          <div className="absolute inset-0 bg-gradient-to-b from-gray-800 to-gray-900 flex items-center justify-center">
            <Building2 className="w-24 h-24 text-gray-700" />
          </div>
        )}

        {/* Price badge */}
        <div className="absolute top-20 right-4 z-10">
          <div className="bg-green-600/90 backdrop-blur-sm px-3 py-1.5 rounded-lg">
            <span className="text-lg font-bold">{formatPrice(listing.price)}</span>
          </div>
        </div>

        {/* Content overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-5 z-10">
          <div className="backdrop-blur-sm bg-black/40 rounded-xl p-4">
            {/* Title */}
            <h2 className="text-xl font-bold leading-tight mb-2 line-clamp-2">
              {listing.title}
            </h2>

            {/* Key stats */}
            <div className="flex flex-wrap gap-3 text-sm text-white/90 mb-2">
              {listing.rooms && (
                <span className="flex items-center gap-1">
                  <BedDouble className="w-4 h-4" />
                  {listing.rooms} Zi.
                </span>
              )}
              {listing.area && (
                <span className="flex items-center gap-1">
                  <Ruler className="w-4 h-4" />
                  {listing.area} m\u00B2
                </span>
              )}
              {listing.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {listing.location}
                </span>
              )}
              {listing.yearBuilt && listing.yearBuilt !== "0" && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {listing.yearBuilt}
                </span>
              )}
            </div>

            <Tags listing={listing} />

            {/* Description toggle */}
            {listing.description && (
              <div className="mt-3">
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-xs text-white/70 hover:text-white transition-colors"
                >
                  {expanded ? (
                    <>
                      <ChevronUp className="w-3 h-3" /> Weniger
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-3 h-3" /> Beschreibung
                    </>
                  )}
                </button>
                {expanded && (
                  <p className="text-sm text-white/80 mt-2 max-h-40 overflow-y-auto leading-relaxed">
                    {listing.description}
                  </p>
                )}
              </div>
            )}

            {/* Link to expose */}
            <a
              href={listing.exposeUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 mt-3 text-sm text-white hover:text-blue-300 transition-colors"
            >
              <ExternalLink className="w-4 h-4" />
              Auf ImmoScout24 ansehen
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
