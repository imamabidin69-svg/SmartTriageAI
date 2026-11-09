import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Access token (15 menit) dan refresh token (8 jam) dari POST /auth/login dengan header X-Client: mobile.
class TokenSesi {
  const TokenSesi({required this.akses, required this.refresh});

  final String akses;
  final String refresh;
}

abstract interface class PenyimpananToken {
  Future<TokenSesi?> baca();
  Future<void> simpan(TokenSesi token);
  Future<void> gantiAkses(String akses);
  Future<void> hapus();
}

/// Token disimpan di flutter_secure_storage (Keystore Android), bukan penyimpanan biasa (NFR-01).
class PenyimpananTokenAman implements PenyimpananToken {
  PenyimpananTokenAman([FlutterSecureStorage? penyimpanan])
    : _penyimpanan = penyimpanan ?? const FlutterSecureStorage();

  static const _kunciAkses = 'token_akses';
  static const _kunciRefresh = 'token_refresh';

  final FlutterSecureStorage _penyimpanan;

  @override
  Future<TokenSesi?> baca() async {
    final akses = await _penyimpanan.read(key: _kunciAkses);
    final refresh = await _penyimpanan.read(key: _kunciRefresh);
    if (akses == null || refresh == null) return null;
    return TokenSesi(akses: akses, refresh: refresh);
  }

  @override
  Future<void> simpan(TokenSesi token) async {
    await _penyimpanan.write(key: _kunciAkses, value: token.akses);
    await _penyimpanan.write(key: _kunciRefresh, value: token.refresh);
  }

  @override
  Future<void> gantiAkses(String akses) => _penyimpanan.write(key: _kunciAkses, value: akses);

  @override
  Future<void> hapus() async {
    await _penyimpanan.delete(key: _kunciAkses);
    await _penyimpanan.delete(key: _kunciRefresh);
  }
}

/// Penyimpanan di memori, dipakai di tes.
class PenyimpananTokenMemori implements PenyimpananToken {
  PenyimpananTokenMemori([this._token]);

  TokenSesi? _token;

  @override
  Future<TokenSesi?> baca() async => _token;

  @override
  Future<void> simpan(TokenSesi token) async => _token = token;

  @override
  Future<void> gantiAkses(String akses) async {
    final lama = _token;
    if (lama != null) _token = TokenSesi(akses: akses, refresh: lama.refresh);
  }

  @override
  Future<void> hapus() async => _token = null;
}
