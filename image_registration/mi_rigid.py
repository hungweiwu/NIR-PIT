import SimpleITK as sitk
import os

# import matplotlib.pyplot as plt


def print_image_info(title, image):
    """print the basic spatial information of the image"""
    print(f"--- {title} ---")
    print(f"  Origin:    {image.GetOrigin()}")
    print(f"  Spacing:   {image.GetSpacing()}")
    print(f"  Size:      {image.GetSize()}")
    print(f"  Direction: {image.GetDirection()}")
    print(f"  PixelType: {image.GetPixelIDTypeAsString()}")


def automatic_registration(fixed_image, moving_image, out_dir):
    """
    execute image registration (CT and MRI)
    use Mattes Mutual Information (mutual information) as the metric standard
    """
    # initialize transformation: align the geometric center of the two images as the starting point
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image,
        moving_image,
        sitk.Euler3DTransform(),
        # sitk.AffineTransform(3),
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )

    # initial_transform = sitk.Euler3DTransform()

    # set registration engine
    registration_method = sitk.ImageRegistrationMethod()

    metric_values = []

    def metric_callback(registration_method):
        metric_values.append(-registration_method.GetMetricValue())
        print(f"Metric Value: {metric_values[-1]}")

    # similarity metric (Metric): mutual information method commonly used for CT/MRI different modalities
    registration_method.SetMetricAsMattesMutualInformation(
        numberOfHistogramBins=50
    )
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(
        0.01
    )  # sample 1% of pixels to accelerate calculation
    registration_method.AddCommand(
        sitk.sitkIterationEvent,
        lambda method=registration_method: metric_callback(method),
    )
    # interpolator
    registration_method.SetInterpolator(sitk.sitkLinear)

    # optimizer (Optimizer): gradient descent method
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10,
    )
    # automatically balance the step size of rotation and translation
    registration_method.SetOptimizerScalesFromPhysicalShift()
    # set initial transformation
    registration_method.SetInitialTransform(initial_transform, inPlace=False)

    print("Executing registration...")

    # Rigid
    final_rigid_transform = registration_method.Execute(
        fixed_image, moving_image
    )
    final_transform = final_rigid_transform

    # plt.figure(figsize=(10, 6))
    # plt.plot(metric_values, marker="o", linestyle="-", color="b", markersize=4)
    # plt.title("Mattes Mutual Information Convergence", fontsize=14)
    # plt.xlabel("Iteration", fontsize=12)
    # plt.ylabel("Metric Value (MI)", fontsize=12)
    # plt.grid(True, linestyle="--", alpha=0.7)

    # plot_path = os.path.join(out_dir, "registration_convergence.png")
    # plt.savefig(plot_path)
    # print(f"Convergence plot saved as: {plot_path}")

    # print result diagnosis
    print(
        f"  Stop Condition: {registration_method.GetOptimizerStopConditionDescription()}"
    )
    print(f"  Final Metric: {-1 *registration_method.GetMetricValue()}")

    return final_transform


def evaluate_alignment_quality(ct_image, mri_aligned):

    def get_clean_body_mask(image, is_ct=True):

        if is_ct:
            binary_mask = image > -300
        else:
            otsu_filter = sitk.OtsuThresholdImageFilter()
            otsu_filter.SetInsideValue(0)
            otsu_filter.SetOutsideValue(1)
            binary_mask = otsu_filter.Execute(image)

        binary_mask = sitk.BinaryFillhole(binary_mask)
        component_image = sitk.ConnectedComponent(binary_mask)

        relabel_filter = sitk.RelabelComponentImageFilter()
        relabel_filter.SetSortByObjectSize(True)
        labeled_image = relabel_filter.Execute(component_image)

        clean_mask = labeled_image == 1

        clean_mask = sitk.BinaryFillhole(clean_mask)

        return clean_mask

    ct_body_mask = get_clean_body_mask(ct_image)
    mri_body_mask = get_clean_body_mask(mri_aligned, is_ct=False)

    ct_body_mask_restricted = ct_body_mask * mri_body_mask
    overlap_filter = sitk.LabelOverlapMeasuresImageFilter()
    overlap_filter.Execute(ct_body_mask_restricted, mri_body_mask)

    dice_val = overlap_filter.GetDiceCoefficient()
    jaccard_val = overlap_filter.GetJaccardCoefficient()

    print(f"\n--- Alignment Quality Metrics ---")
    print(f"  Dice Coefficient:    {dice_val:.4f}")
    print(f"  Jaccard Coefficient: {jaccard_val:.4f}")

    return ct_body_mask, mri_body_mask


def save_masks_for_qc(ct_body_mask, mri_body_mask, out_dir, is_skin=False):

    ct_mask_uint8 = sitk.Cast(ct_body_mask, sitk.sitkUInt8)
    mri_mask_uint8 = sitk.Cast(mri_body_mask, sitk.sitkUInt8)

    if is_skin:
        sitk.WriteImage(
            ct_mask_uint8,
            os.path.join(out_dir, "QC_mask_CT_skin.nrrd"),
            useCompression=True,
        )
        sitk.WriteImage(
            mri_mask_uint8,
            os.path.join(out_dir, "QC_mask_MRI_skin.nrrd"),
            useCompression=True,
        )
    else:
        sitk.WriteImage(
            ct_mask_uint8,
            os.path.join(out_dir, "QC_mask_CT_body.nrrd"),
            useCompression=True,
        )
        sitk.WriteImage(
            mri_mask_uint8,
            os.path.join(out_dir, "QC_mask_MRI_body.nrrd"),
            useCompression=True,
        )

    print(f"QC Masks saved to: {out_dir}")


def main():
    # path setting
    case_id = "case_01"
    base_dir = f"data/HaN/{case_id}"
    ct_file = os.path.join(base_dir, f"{case_id}_IMG_CT.nrrd")
    mri_file = os.path.join(base_dir, f"{case_id}_IMG_MR_T1.nrrd")
    out_dir = os.path.join(base_dir, f"processed_{case_id}")

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # load images
    print("Loading images...")
    ct_raw = sitk.ReadImage(ct_file)
    mri_raw = sitk.ReadImage(mri_file)
    print_image_info("Raw Fixed Image (CT)", ct_raw)
    print_image_info("Raw Moving Image (MRI)", mri_raw)
    # preprocessing
    # convert image to Float32 for mathematical operation
    ct = sitk.Cast(ct_raw, sitk.sitkFloat32)

    # MRI brightness shift for calculation, and convert to Float32
    mri_array = sitk.GetArrayFromImage(mri_raw)
    mri_zeroed = sitk.Cast(mri_raw, sitk.sitkFloat32) - float(mri_array.min())

    # registration
    final_tx = automatic_registration(ct, mri_zeroed, out_dir)

    # resample: MRI in its original space
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(
        ct
    )  # use MRI itself as the reference / mri_zeroed
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetTransform(final_tx)

    mri_aligned = resampler.Execute(mri_zeroed)
    mri_aligned = sitk.Cast(mri_aligned, mri_raw.GetPixelID())

    # evaluate alignment quality
    ct_body_mask, mri_body_mask = evaluate_alignment_quality(ct, mri_aligned)
    save_masks_for_qc(ct_body_mask, mri_body_mask, out_dir)

    print_image_info("Aligned Image (MRI)", mri_aligned)
    # save results
    sitk.WriteImage(
        ct, os.path.join(out_dir, "CT_fixed.nrrd"), useCompression=True
    )
    sitk.WriteImage(
        mri_aligned,
        os.path.join(out_dir, "MRI_aligned.nrrd"),
        useCompression=True,
    )
    sitk.WriteTransform(
        final_tx, os.path.join(out_dir, "mri_to_ct_transform.tfm")
    )
    print(f"\nSaved results to: {out_dir}")
    print(f"Output Size: {mri_aligned.GetSize()}")


if __name__ == "__main__":
    main()
