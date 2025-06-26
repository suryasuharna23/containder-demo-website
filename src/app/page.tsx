// src/app/page.js

import Kamera from "@/components/camera"; // Import komponen Kamera yang sudah kita buat

export default function HomePage() {
  return (
    <main className="relative w-full h-screen flex flex-col items-center justify-center bg-white font-sans">
      <header className="absolute top-0 left-0 w-full h-16 flex items-center pl-8">
        <h2>
          <img src="/containder-logo.png" alt="Containder Logo" className="h-20 mt-10" />
        </h2>
      </header>
      {/* Kotak kamera seperti kamera HP */}
      <div className="relative rounded-xl overflow-hidden shadow-lg border-4 border-white" style={{ width: 320, height: 427 }}>
        {/* Rasio 3:4, misal 320x427px */}
        <Kamera />
      </div>
      {/* Elemen lain di atas kamera */}
      <div className="mt-8 flex flex-col items-center text-white">
        <h1 className="text-4xl md:text-6xl font-bold bg-black bg-opacity-50 p-4 rounded-lg">
          Selamat Datang!
        </h1>
        <p className="mt-4 text-lg  bg-opacity-50 p-2 rounded-lg">
          Website ini langsung mengaktifkan kamera Anda.
        </p>
      </div>
    </main>
  );
}