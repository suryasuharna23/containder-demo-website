import Kamera from "@/components/camera";

export default function HomePage() {
  return (
    <main className="relative w-full min-h-screen flex flex-col bg-gradient-to-br from-blue-50 to-green-50 font-sans">
      {/* Header dengan backdrop blur untuk efek modern */}
      <header className="sticky top-0 z-50 w-full h-20 flex items-center px-6 md:px-8 bg-white/80 backdrop-blur-md border-b border-gray-200/50 shadow-sm">
        <div className="flex items-center gap-3">
          <img src="/containder-logo.png" alt="Containder Logo" className="h-12 w-auto" />
          <div className="hidden md:block">
            <h2 className="text-xl font-semibold text-gray-800">Containder</h2>
            <p className="text-sm text-gray-600">AI Plastic Sorting</p>
          </div>
        </div>
      </header>

      {/* Content area dengan better spacing */}
      <div className="flex-1 flex flex-col items-center justify-start py-8 px-4">
        {/* Welcome section dengan animasi */}
        <div className="w-full max-w-4xl text-center mb-8 animate-fade-in">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-800 mb-4">
            Welcome back!
          </h1>
          <p className="mx-auto max-w-2xl text-sm md:text-base lg:text-lg text-gray-600 leading-relaxed px-6 py-4 bg-white rounded-2xl shadow-md border border-gray-100">
            Our AI-driven technology revolutionizes plastic bottle sorting, minimizing landfill waste and maximizing resource recovery for a healthier planet.
          </p>
        </div>

        {/* Camera component */}
        <Kamera />
      </div>

      {/* Footer optional */}
      <footer className="py-4 text-center text-xs text-gray-500 bg-white/50">
        Powered by AI Technology
      </footer>
    </main>
  );
}