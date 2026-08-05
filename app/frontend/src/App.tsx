import { useEffect, useRef, useCallback, useState } from "react";
import { PropertyCard } from "./components/PropertyCard";
import { Loader2 } from "lucide-react";
import { Listing } from "./types";

const BATCH_SIZE = 5;

function App() {
  const [allListings, setAllListings] = useState<Listing[]>([]);
  const [listings, setListings] = useState<Listing[]>([]);
  const [loading, setLoading] = useState(true);
  const [index, setIndex] = useState(0);
  const observerTarget = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/listings.json")
      .then((r) => r.json())
      .then((data: Listing[]) => {
        setAllListings(data);
        setListings(data.slice(0, BATCH_SIZE));
        setIndex(BATCH_SIZE);
        setLoading(false);
      });
  }, []);

  const loadMore = useCallback(() => {
    if (index >= allListings.length) return;
    const next = allListings.slice(index, index + BATCH_SIZE);
    setListings((prev) => [...prev, ...next]);
    setIndex((prev) => prev + BATCH_SIZE);
  }, [index, allListings]);

  const handleObserver = useCallback(
    (entries: IntersectionObserverEntry[]) => {
      const [target] = entries;
      if (target.isIntersecting && !loading) {
        loadMore();
      }
    },
    [loading, loadMore]
  );

  useEffect(() => {
    const observer = new IntersectionObserver(handleObserver, {
      threshold: 0.1,
      rootMargin: "100px",
    });
    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }
    return () => observer.disconnect();
  }, [handleObserver]);

  return (
    <div className="h-screen w-full bg-black text-white overflow-y-scroll snap-y snap-mandatory hide-scroll">
      <div className="fixed top-4 left-4 z-50">
        <button
          onClick={() => window.location.reload()}
          className="text-2xl font-bold text-white drop-shadow-lg hover:opacity-80 transition-opacity"
        >
          ImmoTok
        </button>
        <p className="text-xs text-white/60">Stuttgart</p>
      </div>

      <div className="fixed top-4 right-4 z-50 text-xs text-white/50">
        {listings.length} / {allListings.length} Angebote
      </div>

      {listings.map((listing) => (
        <PropertyCard key={listing.id} listing={listing} />
      ))}

      <div ref={observerTarget} className="h-10 -mt-1" />
      {loading && (
        <div className="h-screen w-full flex items-center justify-center gap-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Laden...</span>
        </div>
      )}
    </div>
  );
}

export default App;
