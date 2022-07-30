

import cv2
import numpy as np
import pytesseract

from utils import check_pattern


class Ocr:


    def __init__(self, logger, tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.logger=logger

    def clean_image(self, img):
        h, w, c = img.shape
        topleft = round(w * 3 / 4), round(h * 3 / 4)
        bottomright = w, h
        cv2.rectangle(
            img,
            topleft,
            bottomright,
            (255, 255, 255),
            -1
        )
    # def load_image_and_process(self, filepath):
    #     img = cv2.imread(filepath)
    #     self.clean_image(img)
    #     grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #     ret, thresh = cv2.threshold(grayscale, 9, 255, cv2.THRESH_BINARY)
    #     opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, (5, 5), iterations=5)
    #
    #     #opened = cv2.GaussianBlur(opened, (11, 11), 0)
    #
    #     return opened
    def load_image_and_process(self, filepath):
        # img = cv2.imread(filepath)
        # self.clean_image(img)
        #
        # grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # ret, thresh = cv2.threshold(grayscale, 10, 255, cv2.THRESH_BINARY)
        #
        # opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, (5, 5), iterations=5)
        #
        #
        # #ret ,threshGauss =  cv2.threshold(opened, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        #
        # scale_percent = 200
        # width = int(img.shape[1] * scale_percent / 100)
        # height = int(img.shape[0] * scale_percent / 100)
        # dsize = (width, height)
        # output = cv2.resize(opened, dsize, interpolation=cv2.INTER_AREA)
        img = cv2.imread(filepath)
        self.clean_image(img)
        grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(grayscale, 5, 255, cv2.THRESH_BINARY)
        opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, (5, 5), iterations=5)


        # output=opened
        # extracted_text=self.extract_text(output)
        # pat=check_pattern(extracted_text)
        # if not pat:
        #     self.show_img_on_window(output)

        #self.show_img_on_window(threshGauss)

        #self.show_img_on_window(output)
        return opened



    def extract_text(self, img):

        custom_config = r'--psm 4 -c tessedit_char_blacklist=t|;{},o'
        extracted = pytesseract.image_to_string(img, config=custom_config)
        stripped = extracted.strip().replace(" ", "").replace("\n", "")


        self.logger.info(f"Text extracted: {stripped}")
        return stripped
    def extract_text_no_strip(self, img):

        extracted = pytesseract.image_to_string(img)
        self.logger.info(f"Text extracted: {extracted}")
        return extracted

    def extract_data(self, filepath):
        processed = self.load_image_and_process(filepath)
        text = self.extract_text(processed)


        return text



    def show_img_on_window_by_path(self, file_path, wnd_img='image'):
        img = cv2.imread(file_path, 0)

        cv2.imshow(wnd_img, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def show_img_on_window(self, file, wnd_img='image'):
        cv2.namedWindow(wnd_img, cv2.WINDOW_NORMAL)
        cv2.imshow(wnd_img, file)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
