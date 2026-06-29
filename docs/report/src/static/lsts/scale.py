def _scale_images(
        self,
        images: list[Image],
        neural_scale_factors: list[int | None],
        new_size: tuple[int, int]
    ) -> list[Image]:
    if len(images) != len(neural_scale_factors):
        err_msg = f"Number of images and neural scale factors must be the same. Got {len(images)} images and {len(neural_scale_factors)} neural scale factors."
        raise ValueError(err_msg)
    
    n_service = self.neural_scale_service
    int_service = self.interpolation_scale_service
    proc_imgs = []
    for img, nsf in zip(images, neural_scale_factors):
        proc_img = img
        if nsf is not None:
            proc_img = n_service.scale_by_factor(
                proc_img,
                nsf
            )
        proc_imgs.append(
            int_service.scale_to_size(
                proc_img, 
                new_size
            )
        )
    
    return proc_imgs