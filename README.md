# Su Yuzey Alani Hesabı
## Usage (English)

1. Start the app and open `http://localhost:5001`.
2. Draw a polygon on the map to define the area of interest.
3. For **Image 1** and **Image 2**, select:
   - Satellite: **Sentinel-1** (VV/VH) or **Sentinel-2** (NDWI/MNDWI)
   - Year and month (the app uses the selected month’s time window)
4. Click **“Karşılaştır”** to run the analysis.
5. The app applies **Otsu thresholding** to create a water mask and computes the **water area (km²)** for each selection. Results appear in the top-left overlay and masks are rendered on the map.

> Notes:
> - Sentinel-1 water is typically identified as **values below** the Otsu threshold (lower backscatter).
> - Sentinel-2 water is typically identified as **values above** the Otsu threshold (NDWI/MNDWI).
> - Cloud filtering is applied for Sentinel-2 (`CLOUDY_PIXEL_PERCENTAGE < 10`).

---

## Kullanım (Türkçe)

1. Uygulamayı başlatın ve `http://localhost:5001` adresini açın.
2. İlgi alanınızı belirlemek için harita üzerinde bir poligon çizin.
3. **Görüntü 1** ve **Görüntü 2** için şu seçimleri yapın:
   - Uydu: **Sentinel-1** (VV/VH) veya **Sentinel-2** (NDWI/MNDWI)
   - Yıl ve ay (uygulama seçilen ay için zaman aralığını kullanır)
4. **“Karşılaştır”** düğmesine basın.
5. Uygulama, **Otsu eşiği** ile su maskesi oluşturur ve her seçim için **su alanını (km²)** hesaplar. Sonuçlar sol üstteki kutuda gösterilir ve maskeler haritada görselleştirilir.

> Notlar:
> - Sentinel-1’de su genellikle **eşik altındaki** değerlerle (düşük geri saçılım) tanımlanır.
> - Sentinel-2’de su genellikle **eşik üzerindeki** değerlerle (NDWI/MNDWI) tanımlanır.
> - Sentinel-2 için bulut filtresi uygulanır (`CLOUDY_PIXEL_PERCENTAGE < 10`).
