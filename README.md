# XOX Oyunu

Python 3 ile çalışır; ek paket gerekmez. `python xox.py` komutuyla açın.

## Oyun modları

- **Aynı bilgisayar:** X ve O sırayla aynı pencerede oynar.
- **Bilgisayara karşı:** Siz X'siniz; bilgisayar O olarak en iyi hamleyi seçer.
- **Ağda ev sahibi / Ağa katıl:** Ev sahibi X, katılan O olur. İki bilgisayar aynı yerel ağda olmalıdır. Ev sahibi bir port seçip oyunu başlatır; diğer oyuncu ev sahibinin yerel IP adresini ve aynı portu girerek bağlanır. Güvenlik duvarı bağlantı izni isteyebilir.

**Zaman modu:** Her oyuncu 60 saniyeyle başlar. Yalnızca sırası gelen oyuncunun süresi azalır. Hamle sonrası ek süre verilmez. Süre sıfıra ulaşırsa o oyuncu kaybeder; oyun bitince saatler durur. Yeni oyunda iki saat de 60 saniyeye döner. Süre çubukları 60 saniyeyi temel alır. Ağ oyununda zaman modunu ev sahibi belirler.

Oyun modunu değiştirmek veya zaman modu kutusunu açıp kapatmak yeni oyunu hemen başlatır. Aynı ayarlarla tekrar oynamak için **Yeni oyun** düğmesine basın. Ağ oyunu yeniden başlatıldığında iki tarafta da tekrar bağlantı kurulmalıdır.

Arayüz sıradaki oyuncuyu ve zaman modu açıksa iki oyuncunun kalan süresini gösterir. Bilgisayara karşı modda “Sen: X — Bilgisayar: O” ve “Sıra sende / Bilgisayar düşünüyor” görünür; IP ve port alanları yalnızca ağ modlarında görünür. X mavi, O kırmızıdır. Kazanan çizginin üç hücresi yeşil vurgulanır; sonuç üstte tek mesajla gösterilir. **Yeni oyun** düğmesi seçili ayarlarla oyunu yeniden başlatır.

## Üç test senaryosu

`python -m unittest -v test_xox.py` komutuyla otomatik testleri çalıştırın.

| Senaryo | Adımlar | Beklenen sonuç |
|---|---|---|
| 1. İki oyuncu ve dolu kare | X:0, O:3, X:1, O:4, X:2 oynayın; sonra 5'e hamle deneyin. | X yatay çizgiyle kazanır; oyun bitince yeni hamle kabul edilmez. |
| 2. Bilgisayarın kazanma hamlesi | O'nun 0 ve 1'de, X'in 3 ve 4'te olduğu konumda bilgisayara hamle yaptırın. | Bilgisayar 2'yi seçip kazanır. |
| 3. Ağ ve zaman modu | İki bilgisayarda aynı portla ev sahibi ve katılan olarak bağlanın; zaman modunu açın. X 5 saniye sonra hamle yapsın, O dolu kareye bassın ve sonra süresi bitsin. | X hamlesi iki ekranda görünür ve X saati 55 saniyeye iner; geçersiz hamle süre eklemez; O'nun süresi bitince X kazanır ve iki saat durur. Otomatik test zaman kuralını doğrular; iki bilgisayarlı bağlantı adımları elle uygulanır. |

