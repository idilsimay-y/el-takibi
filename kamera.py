import cv2
import random
import mediapipe as mp

mp_el = mp.solutions.hands
cizim = mp.solutions.drawing_utils
el_modeli = mp_el.Hands(max_num_hands=2, min_detection_confidence=0.7)

uc_noktalar = [8, 12, 16, 20]

YAZI_TIPI = cv2.FONT_HERSHEY_DUPLEX

# Renkler BGR sırasıyla (OpenCV'de renkler B-G-R yazılır)
FUSYA = (110, 0, 214)           # koyu pembe: Toplam yazısı
ACIK_PEMBE = (205, 170, 255)    # açığa yakın pembe: sonuç yazısı
TOZ_PEMBE = (235, 225, 255)     # toz pembe: Sen / Bilgisayar
EL_RENGI = (255, 255, 0)        # elin yanındaki sayı

secenekler = {0: "TAS", 2: "MAKAS", 5: "KAGIT"}
yener = {"TAS": "MAKAS", "MAKAS": "KAGIT", "KAGIT": "TAS"}
oyuncu_yazi = ""
bilgisayar_yazi = ""
sonuc_yazi = "Bosluk tusuna basiniz."


def yazi_yaz(kare, metin, x, y, boyut, renk, kalinlik=2, sagda=False):
    # sagda=True ise x, "sağ kenardan boşluk" demek olur
    # yaziyi boyutunu piksele göre ayarlarız
    #eğer sağda olacaksa önceden yazının genişliği ve yüksekliği bilinmeli ki başlayacağı x noktasını belirleyebilelim
    if sagda:
        genislik = cv2.getTextSize(metin, YAZI_TIPI, boyut, kalinlik)[0][0]
        x = kare.shape[1] - genislik - x
    # Önce kalın siyah yazı (kenarlık), üstüne renkli yazı
    cv2.putText(kare, metin, (int(x), int(y)), YAZI_TIPI, boyut, (0, 0, 0), kalinlik + 3)
    cv2.putText(kare, metin, (int(x), int(y)), YAZI_TIPI, boyut, renk, kalinlik)

#kamerayı açar ve ekrana doldurmasını sağlar
kamera = cv2.VideoCapture(0)
cv2.namedWindow("Kamera", cv2.WINDOW_NORMAL)

while True:
    basarili, kare = kamera.read()
    if not basarili:
        break

    #görüntüyü ters çevirir
    kare = cv2.flip(kare, 1)

    #opencv ve mediapipe renk dizilimi farkını kaldırmak için dönüşüm yapar
    rgb = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
    sonuc = el_modeli.process(rgb)

    toplam_parmak = 0

    if sonuc.multi_hand_landmarks:
        for i, el in enumerate(sonuc.multi_hand_landmarks):
            cizim.draw_landmarks(kare, el, mp_el.HAND_CONNECTIONS)
            #hangi nokta birbirine bağlanacak ayarlar

            taraf = sonuc.multi_handedness[i].classification[0].label
            #hem sıradan(i) hem de hangi el olduğundan(el) aldığı bilgiyle left/right yazısını çıkartır

            noktalar = el.landmark
            bu_elin_parmagi = 0

            #dört parmak için açıklık kontrolü
            for uc in uc_noktalar:
                if noktalar[uc].y < noktalar[uc - 2].y:
                    bu_elin_parmagi += 1

            #başparmak için açıklık kontrolü
            if taraf == "Right":
                if noktalar[4].x < noktalar[3].x:
                    bu_elin_parmagi += 1
            else:
                if noktalar[4].x > noktalar[3].x:
                    bu_elin_parmagi += 1

            toplam_parmak += bu_elin_parmagi

            #yazıyı yazacağı yeri piksele adapte eder ve konumunu ayarlar
            bilek_x = int(noktalar[0].x * kare.shape[1])
            bilek_y = int(noktalar[0].y * kare.shape[0])
            yazi_yaz(kare, f"{taraf}: {bu_elin_parmagi}", bilek_x - 40, bilek_y + 40,
                     0.8, EL_RENGI, 2)

    # Sağ üst: toplam
    yazi_yaz(kare, f"Toplam: {toplam_parmak}", 20, 60, 1.5, FUSYA, 3, sagda=True)

    # Sol üst: oyun yazıları, alt alta
    yazi_yaz(kare, f"Sen: {oyuncu_yazi}", 20, 50, 1.0, TOZ_PEMBE, 2)
    yazi_yaz(kare, f"Bilgisayar: {bilgisayar_yazi}", 20, 95, 1.0, TOZ_PEMBE, 2)
    yazi_yaz(kare, sonuc_yazi, 20, 145, 1.2, ACIK_PEMBE, 2)

    #üstüne yazı ve çizimler olan kareyi gösterir
    cv2.imshow("Kamera", kare)

    #klavye getirilerini kontrol eder ve pencere yenilemeyi sağlar
    tus = cv2.waitKey(1) & 0xFF
    if tus == ord("q"):
        break
    #q tuşuna basınca döngüden çıkılır

    #boşluk tuşuna basınca olan asıl oyun kuralı
    if tus == 32:
        if toplam_parmak in secenekler:
            oyuncu_yazi = secenekler[toplam_parmak]
            bilgisayar_yazi = random.choice(["TAS", "KAGIT", "MAKAS"])

            if oyuncu_yazi == bilgisayar_yazi:
                sonuc_yazi = "BERABERE"
            elif yener[oyuncu_yazi] == bilgisayar_yazi:
                sonuc_yazi = "KAZANDIN!"
            else:
                sonuc_yazi = "KAYBETTIN"
        else:
            sonuc_yazi = "0, 2 veya 5 parmak goster"

    #pencere hala görünür mü diye sorgular
    if cv2.getWindowProperty("Kamera", cv2.WND_PROP_VISIBLE) < 1:
        break

kamera.release()
cv2.destroyAllWindows()
