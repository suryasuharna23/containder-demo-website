// src/app/page.js

import Kamera from "@/components/camera"; // Import komponen Kamera yang sudah kita buat

export default function HomePage() {
  return (
    <main className="relative w-full h-screen flex flex-col items-center justify-center bg-white font-sans">
      <header className="flex top-0 left-0 w-full h-16 flex items-center pl-8">
        <h2>
          <img src="/containder-logo.png" alt="Containder Logo" className="h-20 mt-10" />
        </h2>
      </header>
      {/* Kotak kamera seperti kamera HP */}
      {/* Elemen lain di atas kamera */}
      <div className="mt-8 flex flex-col items-center text-black">
        <h1 className="text-4xl md:text-6xl font-bold p-4 rounded-lg">
          Welcome back!
        </h1>
        <p className="mx-12 mb-10 max-w-xl w-full text-lg md:text-xl text-center p-4 rounded-lg bg-white shadow-lg">
          Our AI-driven technology revolutionizes plastic bottle sorting, minimizing landfill waste and maximizing resource recovery for a healthier planet.
        </p>
      </div>
      <div className="relative rounded-xl overflow-hidden shadow-lg border-4 border-white" style={{ width: 320, height: 427 }}>
        {/* Rasio 3:4, misal 320x427px */}
        <Kamera />
      </div>
    </main>
  );
}