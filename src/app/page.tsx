// src/app/page.js

import Kamera from "@/components/camera"; // Import komponen Kamera yang sudah kita buat

export default function HomePage() {
  return (
    <main className="relative w-full h-screen flex flex-col items-center justify-center bg-gray-900">
      {/* Kotak kamera seperti kamera HP */}
      <div className="relative rounded-2xl overflow-hidden shadow-lg border-4 border-white" style={{ width: 320, height: 427 }}>
        {/* Rasio 3:4, misal 320x427px */}
        <Kamera />
      </div>
      {/* Elemen lain di atas kamera */}
      <div className="mt-8 flex flex-col items-center text-white">
        <h1 className="text-4xl md:text-6xl font-bold bg-black bg-opacity-50 p-4 rounded-lg">
          Selamat Datang!
        </h1>
        <p className="mt-4 text-lg bg-black bg-opacity-50 p-2 rounded-lg">
          Website ini langsung mengaktifkan kamera Anda.
        </p>
      </div>
    </main>
  );
}