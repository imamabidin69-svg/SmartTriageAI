/// Pengaturan yang dibaca saat build lewat --dart-define, supaya alamat server tidak ditulis di kode.
///
/// Contoh: flutter run --dart-define=API_BASE_URL=http://192.168.1.10:5000
/// Bawaannya 10.0.2.2, yaitu alamat laptop bila aplikasi dijalankan di emulator Android.
const String alamatApi = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:5000');

/// Daftar tunggu dan peringatan dimuat ulang setiap 15 detik selama aplikasi dibuka (Desain 2.7).
const Duration jedaMuatUlangAntrean = Duration(seconds: 15);

/// Batas waktu tunggu satu request. Klasifikasi dan pemindaian bisa butuh beberapa detik di server.
const Duration batasWaktuRequest = Duration(seconds: 30);
