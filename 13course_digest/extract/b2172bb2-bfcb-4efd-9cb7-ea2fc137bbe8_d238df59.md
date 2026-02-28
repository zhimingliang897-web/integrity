## More Examples

<div>Series 1</div>

![](extract/subset_16_20_6ee3307d_669bdb5d/images/page_1_img_in_chart_box_65_340_754_962.jpg)

## ARMA( , ) AR167

<div>Series x</div>

![](extract/subset_16_20_6ee3307d_669bdb5d/images/page_1_img_in_chart_box_783_339_1466_961.jpg)

## More Examples

<div>Series 1</div>

![](extract/subset_16_20_6ee3307d_669bdb5d/images/page_2_img_in_chart_box_69_329_756_954.jpg)

<div>Series x</div>

![](extract/subset_16_20_6ee3307d_669bdb5d/images/page_2_img_in_chart_box_795_330_1475_955.jpg)

## Practical Considerations of Model Identification (via ACF/PACF)

## Practical identification rules

• Start with low-order models:  $ p, q \in \{0, 1, 2\} $ .

• Prefer AR or MA over ARMA when a clear cutoff is present.

• Avoid large p and q simultaneously.

• Parsimony principle: Among competing models with similar ACF/PACF behavior, choose the one with fewer parameters.

## Limitations of identification via ACF/PACF

• Sample ACF/PACF are noisy for finite N.

Borderline significance is common.

• Different models can produce similar correlation patterns.

## Key message

Model identification provides candidates, not final answers. Final validation relies on estimation quality and residual diagnostics.

## Why Order Selection?

After tentative identification, we must choose concrete orders  $ (p, q) $ .

• Competing models may fit data similarly but differ in complexity.

Order selection balances goodness-of-fit and parsimony.

## Core Tension

Underfitting

Bias,

Overfitting

Variance.

Treating  $ (p,q) $  as hyperparameters, we may use information criteria (IC) to select the order of ARMA $ (p,q) $  models.

## Caveats and Good Practice

• Information criteria rely on correct likelihood specification.

• Near-unit-root or near-cancellation cases may distort selection.

Always combine order selection with residual diagnostics (next section).

![](extract/subset_16_20_6ee3307d_669bdb5d/images/page_4_img_in_image_box_1358_872_1514_1075.jpg)

## Likelihood-based Model Comparison

Assume a fitted ARMA(p, q) model

 $$ \phi(B)(X_{t}-\mu)=\theta(B)Z_{t}, $$ 

 $$ Z_{t}\sim W N(0,\sigma^{2}), $$ 

with Gaussian likelihood.

## Definition (Maximized log-likelihood)

Let $\hat{\Theta}_{p,q}$ be the MLE. Define

 $$ \ell_{p,q}=\ell(\hat{\Theta}_{p,q})=-\frac{N}{2}\log(\hat{\sigma}_{p,q}^{2})+C, $$ 

where C does not depend on  $ (p, q) $ .

## Principle

Larger  $ \ell_{p,q} $  indicates better in-sample fit, but ignores model complexity.