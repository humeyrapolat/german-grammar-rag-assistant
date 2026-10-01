# German Grammar RAG Assistant — Test Seti

Bu test seti, chat'e tek tek yapıştırıp cevapları değerlendirmen için hazırlandı. Her soru için **ne beklediğimizi** ve **neden o kategoride olduğunu** belirttim.

Kapsam hatırlatması: kitabın sadece ilk 80 sayfası (Kapitel 10-12 civarı) Pinecone'da indeksli. Şimdiye kadar gördüğümüz konular: Komparativ, Onlineshopping (Vor-/Nachteile), Kleidung online bestellen, Pizza-Lieferung şikayeti, kitabın sembol sayfası (sayfa 2).

---

## Kategori 1 — Temel, Tek Sayfalık Sorular
Amaç: retrieval'ın doğru chunk'ı bulup bulmadığını, cevabın context'e sadık kalıp kalmadığını görmek.

1. **"Was sind die Vor- und Nachteile von Onlineshopping?"**
   *(Zaten test ettik, referans olarak tut — Sayfa 72-73 bekleniyor.)*

2. **"Wie bildet man den Komparativ im Deutschen?"**
   Beklenen: Komparativ konusunun geçtiği sayfa(lar)dan gramer açıklaması + kaynak.

3. **"Was für Symbole gibt es in diesem Buch und was bedeuten sie?"**
   Beklenen: Sayfa 2'deki sembol açıklamaları (Audio, Phonetik, Internetrecherche, Textproduktion, Redemittel, Achtung-Fehler). Bu, gramer dışı bir "kitap yapısı" sorusu — retrieval'ın sadece gramer sayfalarına değil, farklı türde içeriğe de ulaşabildiğini test eder.

---

## Kategori 2 — Çoklu Sayfa / Sentez Gerektiren Sorular
Amaç: birden fazla chunk'tan bilgi birleştirip birleştiremediğini görmek (Basic LLM Chain'in context'teki tüm `[Sayfa X]` bloklarını kullanıp kullanmadığı).

4. **"Lena möchte ein Kleid online bestellen — was muss sie beim Ausfüllen des Formulars beachten, und was könnte dabei schiefgehen (z. B. mit der Lieferung)?"**
   Beklenen: Hem sipariş formu detayları hem de teslimat/gecikme riskleriyle ilgili ayrı sayfalardan bilgi birleştirmesi.

5. **"Was für Probleme können bei einer Online-Bestellung oder -Lieferung auftreten, laut den Beispielen im Buch?"**
   Beklenen: Hem Lena'nın elbise siparişi hem pizza şikayeti örneğini (farklı sayfalar) bir araya getirmesi.

---

## Kategori 3 — Halüsinasyon / Kapsam Dışı Sorular (en kritik kategori)
Amaç: System Message'daki "cevap context'te yoksa bunu açıkça söyle, bilgi uydurma" talimatının gerçekten çalışıp çalışmadığını doğrulamak. Bunlardan biri bile düzgün cevap "üretirse" (uydurursa), bu ciddi bir halüsinasyon sorunu demektir.

6. **"Wie bildet man das Perfekt mit 'haben' und 'sein'?"**
   *(Kitabın indekslenen 80 sayfasında bu konu muhtemelen yok — eğer sistem bunu da anlatırsa, ya gerçekten kitapta var ya da halüsinasyon yapıyor, ikisini ayırt etmen lazım.)*

7. **"Was ist die Hauptstadt von Deutschland?"**
   Beklenen: Kesinlikle context dışı, genel kültür sorusu. Sistem "bu bilgi elimde/context'imde yok" demeli, Berlin diye cevap VERMEMELİ (verirse, ne kadar doğru olursa olsun, bu RAG'ın amacına aykırı — context dışına çıkmış demektir).

8. **"Erkläre mir die Grammatik von Relativsätzen."**
   *(80 sayfalık kapsamda muhtemelen yok — kontrollü bir "yok" testi.)*

9. **"Was ist in Kapitel 15 des Buches?"**
   Beklenen: Kapitel 15 indekste yok (sadece ~Kapitel 10-13 var) — sistem bunu bilmediğini söylemeli, uydurmamalı.

---

## Kategori 4 — Farklı İfade Biçimleri (Robustness)
Amaç: aynı bilgiyi farklı şekillerde sorunca retrieval'ın hâlâ doğru chunk'ı bulup bulamadığını görmek.

10. **"Komparativ nasıl yapılır?"** *(Türkçe soru — İngilizce/Almanca değil)*
    Beklenen: Sistem muhtemelen embedding modelinin çok dilli olup olmamasına bağlı olarak yine doğru chunk'ı bulabilir ya da bulamayabilir — bu ilginç bir sınır testi, cevap kalitesi düşerse bunu not et.

11. **"What's the comparative form in German grammar?"** *(İngilizce)*
    Aynı amaç, İngilizce ile test.

12. **"lena kleid online"** *(kısa, eksik cümle, anahtar kelime gibi)*
    Beklenen: Yine de Lena'nın elbise örneğini bulup bulamadığını test eder — gerçek kullanıcılar bazen böyle eksik yazar.

---

## Kategori 5 — Sınır / Kenar Durumlar

13. **""** *(boş mesaj — eğer chat arayüzü izin veriyorsa)*
    Beklenen: Hata vermeden nazikçe "bir soru yazar mısın" gibi bir şey söylemeli, workflow çökmemeli.

14. **"Fasse alles zusammen, was im Buch steht."** *(çok geniş, belirsiz bir istek)*
    Beklenen: Sistem sadece Top-K (4) chunk getirdiği için kitabın "tamamını" özetleyemeyeceğini görmen lazım — bu, mevcut mimarinin bir sınırlaması (limit=4), düzeltmemiz gereken bir hata değil ama bilmen gereken bir gerçek.

---

## Değerlendirirken Nelere Bakmalısın

Her cevap için üç şeyi kontrol et:
- **Doğruluk:** Context'teki bilgiyle uyumlu mu, yoksa uydurma mı var?
- **Kaynak gösterme:** Cevabın sonunda "Quellen: Sayfa X" satırı var mı, ve gösterdiği sayfalar gerçekten o bilgiyi içeriyor mu (rastgele bir sayfa numarası atmıyor mu)?
- **Dürüstlük (Kategori 3 için özellikle):** Context'te olmayan bir şey sorulduğunda, sistem bunu açıkça itiraf ediyor mu, yoksa genel bilgisinden (training data'sından) cevap mı veriyor?

## Bulunan Hatalar (Debugging Günlüğü)

Test sürecinde sistemin kendisinde üç kritik hata bulundu ve düzeltildi — detaylar `README.md`'de:

1. **Donmuş prompt:** Pinecone'un sorgu alanı her zaman aynı (yanlış) metni aratıyordu, gerçek soru hiç dikkate alınmıyordu.
2. **Footer kirliliği:** Bir sayfa altbilgisindeki tesadüfi "15" rakamı, "Kapitel 15" sorusuna alakasız bir chunk'ın yüksek skorla eşleşmesine sebep oldu.
3. **Hafıza mimarisi:** Basic LLM Chain node'unun doğrudan bir Memory portu olmadığı için, çok turlu konuşma hafızası Chat Memory Manager node'larıyla elle kuruldu.
