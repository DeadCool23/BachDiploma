def reduce_images(
    self,
    images: list[Image]
) -> list[Image]:
    if len(images) == 0:
        return []
    
    if len(images) == 1:
        err_msg = "At least 2 images are required for reduction"
        raise ValueError(err_msg)
    
    imgs_sizes = np.array([img.size for img in images])
    imgs_aspect_ratios = imgs_sizes[:, 0] / imgs_sizes[:, 1]

    aspect_ratios_equal = np.allclose(imgs_aspect_ratios, imgs_aspect_ratios[0])
    if not aspect_ratios_equal:
        err_msg = "All images must have the same aspect ratio"
        raise ValueError(err_msg)

    max_size = np.max(imgs_sizes, axis=0)
    scale_factors = max_size[0] / imgs_sizes[:, 0]
    neural_scale_factors = [
        self._select_neural_factor(sf) for sf in scale_factors
    ]

    return self._scale_images(images, neural_scale_factors, tuple(max_size))