import re

from transformers import Pix2StructForConditionalGeneration, Pix2StructProcessor
from PIL import ImageDraw


class UICaptioner:
    def __init__(self):
        self.model = Pix2StructForConditionalGeneration.from_pretrained("google/pix2struct-widget-captioning-base")
        self.processor = Pix2StructProcessor.from_pretrained("google/pix2struct-widget-captioning-base")
        self.text = ""

    def generate_caption(self, bounds, screenshot):
        image = self.preprocess(bounds, screenshot)
        # image.show()
        inputs = self.processor(text=self.text, images=image, return_tensors="pt")
        predictions = self.model.generate(**inputs, max_new_tokens=50)
        generated_text = self.processor.decode(predictions[0], skip_special_tokens=True)
        #print(generated_text)
        return generated_text

    def preprocess(self, bounds, screenshot):
        xmin, ymin, xmax, ymax = bounds
        # Ensure ymax >= ymin
        if ymax < ymin:
            ymax, ymin = ymin, ymax

        image = screenshot.convert('L')
        image = image.convert('RGB')
        img_draw = ImageDraw.Draw(image, "RGBA")

        # Additional check to ensure y1 >= y0 for drawing
        top_left = (xmin + 5, min(ymin, ymax))
        bottom_right = (xmax - 5, max(ymin, ymax))

        img_draw.rectangle(
            xy=(top_left, bottom_right),
            fill=(0, 0, 255, 0),  # Semi-transparent fill
            outline=(0, 0, 255, 255)  # Solid blue outline
        )
        return image
