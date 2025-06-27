// src/app/page.tsx

import Kamera from "@/components/camera"; // Import komponen Kamera

export default function HomePage() {
  return (
    // Mengubah layout agar halaman bisa di-scroll jika kontennya panjang
    <main className="relative w-full min-h-screen flex flex-col items-center justify-start py-8 bg-white font-sans">
      <header className="relative top-0 left-0 w-full h-16 flex items-center pl-8">
        <h2>
          <img src="/containder-logo.png" alt="Containder Logo" className="h-16 w-auto" />
        </h2>
      </header>
      {/* Elemen lain di atas kamera */}
      <div className="mt-2 w-full flex flex-col items-center text-black">
        <h1 className="text-4xl md:text-3xlxl font-bold p-4 rounded-lg">
          Welcome back!
        </h1>
        <p className="mx-4 md:mx-12 mb-3 max-w-xl w-full text-sm md:text-base text-center p-4 rounded-lg bg-white shadow-lg">
          Our AI-driven technology revolutionizes plastic bottle sorting, minimizing landfill waste and maximizing resource recovery for a healthier planet.
        </p>
      </div>
      
      {/* Komponen Kamera dipanggil langsung tanpa div pembungkus yang membatasi tinggi */}
      <Kamera />

    </main>
  );
}