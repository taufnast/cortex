import matplotlib
import matplotlib.pyplot as plt

###################
# NOT IMPLEMENTED
###################
def parse_depth_image(context, snapshot):
    pass
    path = context.path('depth_image.jpg')
    size = snapshot.color_image.width, snapshot.color_image.height

    fig, ax = plt.subplots()
    im = ax.imshow(snapshot.data)
    plt.savefig(path, pil_kwargsdict={"size": size})
    # ax.set_title("Depth Image")
    fig.tight_layout()
    plt.show()


parse_depth_image.tag = 'depth_image'
