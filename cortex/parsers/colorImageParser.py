from PIL import Image

###################
# NOT IMPLEMENTED
###################
def parse_color_image(context, snapshot):
    pass
    path = context.path('color_image.jpg')
    size = snapshot.color_image.width, snapshot.color_image.height
    image = Image.new('RGB', size)
    image.putdata(snapshot.color_image.data)
    image.save(path)


parse_color_image.tag = 'color_image'
