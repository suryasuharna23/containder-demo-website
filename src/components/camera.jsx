"use client";

import { useEffect, useRef, useState } from 'react';

const Kamera = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [captured, setCaptured] = useState(null);
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const [result, setResult] = useState(null);
  const [processedImage, setProcessedImage] = useState(null); // Untuk gambar hasil deteksi
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const getCameraStream = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          video: { 
            facingMode: "environment", // Kamera belakang
            width: { ideal: 1280 },
            height: { ideal: 720 }
          } 
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err) {
        console.error("Error accessing camera: ", err);
        setError("Tidak dapat mengakses kamera. Pastikan Anda memberikan izin dan kamera terpasang.");
      }
    };

    getCameraStream();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);

  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const imageData = canvas.toDataURL('image/png');
      setCaptured(imageData);
      setError(null);
    }
  };

  const toggleDropdown = () => {
    setDropdownOpen(!isDropdownOpen);
  };

  useEffect(() => {
    if (captured === null) return;
    
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      setProcessedImage(null);
      try {
        const res = await fetch('http://127.0.0.1:8001', {
          method: "POST",
          headers: {"Content-Type":"application/json"},
          body: JSON.stringify({image: captured})
        });
        
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        const data = await res.json();
        
        // Debug: Log data yang diterima
        console.log('Data dari backend:', data);
        
        // Validasi data dari backend yang lebih fleksibel
        if (!data || typeof data !== 'object') {
          throw new Error('Data tidak valid dari server');
        }
        
        // Cek apakah ada gambar hasil deteksi
        if (data.processed_image || data.detection_image || data.contour_image) {
          const processedImg = data.processed_image || data.detection_image || data.contour_image;
          // Pastikan format base64 sudah benar
          const imageWithPrefix = processedImg.startsWith('data:image') ? processedImg : `data:image/png;base64,${processedImg}`;
          setProcessedImage(imageWithPrefix);
        }
        
        // Convert string numbers to actual numbers if needed
        const processedData = {
          classification: data.classification,
          estimated_volume_ml: parseFloat(data.estimated_volume_ml) || 0,
          real_height_cm: parseFloat(data.real_height_cm) || 0,
          real_diameter_cm: parseFloat(data.real_diameter_cm) || 0,
          confidence_percent: parseFloat(data.confidence_percent) || 0
        };
        
        console.log('Processed data:', processedData);
        setResult(processedData);
        
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(error.message || 'Gagal menghubungi server. Pastikan backend berjalan.');
        setResult(null);
        setProcessedImage(null);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, [captured]);

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600 bg-green-100';
    if (confidence >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  if (error && !captured) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-red-50 rounded-2xl border border-red-200">
        <div className="text-red-600 text-center">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
          <p className="text-sm font-medium">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col lg:flex-row items-center justify-center lg:justify-center gap-6 w-full max-w-6xl mx-auto">
      {/* Camera container */}
      <div className="flex-shrink-0">
        <div className="relative mb-6 lg:mb-0">
          <div className="relative w-80 h-96 bg-gradient-to-br from-gray-900 to-black rounded-3xl overflow-hidden shadow-2xl border-4 border-white">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
            
            {/* Camera overlay UI */}
            <div className="absolute inset-0 pointer-events-none">
              {/* Corner indicators */}
              <div className="absolute top-4 left-4 w-6 h-6 border-l-2 border-t-2 border-white/60 rounded-tl-lg"></div>
              <div className="absolute top-4 right-4 w-6 h-6 border-r-2 border-t-2 border-white/60 rounded-tr-lg"></div>
              <div className="absolute bottom-4 left-4 w-6 h-6 border-l-2 border-b-2 border-white/60 rounded-bl-lg"></div>
              <div className="absolute bottom-4 right-4 w-6 h-6 border-r-2 border-b-2 border-white/60 rounded-br-lg"></div>
              
              {/* Center focus indicator */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-16 h-16 border-2 border-white/40 rounded-full"></div>
            </div>

            {/* Capture button */}
            <button
              onClick={handleCapture}
              disabled={isLoading}
              className="absolute left-1/2 -translate-x-1/2 bottom-4 w-16 h-16 bg-white rounded-full shadow-xl flex items-center justify-center transition-all duration-200 hover:scale-105 active:scale-95 disabled:opacity-50"
              aria-label="Capture Photo"
            >
              <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center">
                {isLoading ? (
                  <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <div className="w-3 h-3 bg-white rounded-full"></div>
                )}
              </div>
            </button>
          </div>
          <canvas ref={canvasRef} style={{ display: 'none' }} />
        </div>
      </div>

      {/* Results section */}
      <div className="w-full lg:max-w-md">
        <div className="w-full bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden">
          <button
            onClick={toggleDropdown}
            className="w-full px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white font-medium flex justify-between items-center transition-all duration-200 hover:from-blue-600 hover:to-blue-700"
          >
            <div className="flex items-center gap-3">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span>Hasil Analisis</span>
              {captured && (
                <span className="bg-white/20 text-xs px-2 py-1 rounded-full">
                  {isLoading ? 'Processing...' : error ? 'Error' : result ? 'Ready' : 'Captured'}
                </span>
              )}
            </div>
            <svg
              className={`w-5 h-5 transform transition-transform duration-200 ${
                isDropdownOpen ? 'rotate-180' : ''
              }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {isDropdownOpen && (
            <div className="p-6 bg-gray-50">
              {captured ? (
                <div className="space-y-4">
                  {/* Original and Processed Images */}
                  <div className="grid grid-cols-1 gap-4">
                    {/* Original Image */}
                    <div className="relative">
                      <img
                        src={captured}
                        alt="Foto Asli"
                        className="w-full rounded-xl shadow-md border border-gray-200"
                      />
                      <div className="absolute top-2 left-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                        Original
                      </div>
                    </div>

                    {/* Processed Image with Detection */}
                    {processedImage && (
                      <div className="relative">
                        <img
                          src={processedImage}
                          alt="Hasil Deteksi"
                          className="w-full rounded-xl shadow-md border border-green-200"
                        />
                        <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Deteksi AI
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Loading state */}
                  {isLoading && (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                      <span className="ml-3 text-gray-600">Menganalisis gambar...</span>
                    </div>
                  )}

                  {/* Beautiful result display */}
                  {result && !isLoading && !error && (
                    <div className="space-y-4">
                      {/* Classification Card */}
                      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-gray-800 flex items-center gap-2">
                            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Klasifikasi Botol
                          </h4>
                          <span className={`px-3 py-1 rounded-full text-xs font-medium ${getConfidenceColor(result.confidence_percent)}`}>
                            {result.confidence_percent.toFixed(1)}% akurat
                          </span>
                        </div>
                        <div className="bg-blue-50 p-3 rounded-lg">
                          <span className="text-2xl font-bold text-blue-700">{result.classification}</span>
                        </div>
                      </div>

                      {/* Measurements Grid */}
                      <div className="grid grid-cols-2 gap-3">
                        {/* Volume */}
                        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                          <div className="flex items-center gap-2 mb-2">
                            <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                            </svg>
                            <span className="text-xs font-medium text-gray-500">VOLUME</span>
                          </div>
                          <div className="text-lg font-bold text-purple-700">{result.estimated_volume_ml} mL</div>
                        </div>

                        {/* Height */}
                        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                          <div className="flex items-center gap-2 mb-2">
                            <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7l4-4m0 0l4 4m-4-4v18" />
                            </svg>
                            <span className="text-xs font-medium text-gray-500">TINGGI</span>
                          </div>
                          <div className="text-lg font-bold text-green-700">{result.real_height_cm} cm</div>
                        </div>

                        {/* Diameter */}
                        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm col-span-2">
                          <div className="flex items-center gap-2 mb-2">
                            <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 8h16M4 16h16" />
                            </svg>
                            <span className="text-xs font-medium text-gray-500">DIAMETER</span>
                          </div>
                          <div className="text-lg font-bold text-orange-700">{result.real_diameter_cm} cm</div>
                        </div>
                      </div>

                      {/* Summary Card */}
                      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-xl border border-blue-200">
                        <h5 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Ringkasan
                        </h5>
                        <p className="text-sm text-gray-700">
                          Botol plastik <strong>{result.classification}</strong> dengan volume estimasi <strong>{result.estimated_volume_ml} mL</strong>. 
                          Dimensi: tinggi <strong>{result.real_height_cm} cm</strong>, diameter <strong>{result.real_diameter_cm} cm</strong>.
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Error state */}
                  {error && !isLoading && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                      <div className="flex flex-col items-center gap-3 text-red-700 text-center">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                        </svg>
                        <div>
                          <p className="font-medium text-sm">Analisis Gagal</p>
                          <p className="text-xs text-red-600 mt-1">{error}</p>
                          <button 
                            onClick={() => {
                              setError(null);
                              setCaptured(null);
                              setProcessedImage(null);
                            }}
                            className="mt-3 px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-xs rounded-lg transition-colors"
                          >
                            Ambil Foto Ulang
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* No result state */}
                  {!isLoading && !error && !result && captured && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                      <div className="flex flex-col items-center gap-3 text-yellow-700 text-center">
                        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <div>
                          <p className="font-medium text-sm">Tidak Ada Hasil</p>
                          <p className="text-xs text-yellow-600 mt-1">Server tidak mengembalikan data analisis</p>
                          <button 
                            onClick={() => {
                              setCaptured(null);
                              setProcessedImage(null);
                            }}
                            className="mt-3 px-3 py-1 bg-yellow-100 hover:bg-yellow-200 text-yellow-700 text-xs rounded-lg transition-colors"
                          >
                            Coba Lagi
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <p className="text-gray-500 text-sm">
                    Belum ada gambar yang diambil.
                    <br />
                    <span className="text-xs">Tekan tombol capture untuk mengambil foto.</span>
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Kamera;