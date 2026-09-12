# Demo Recording Script (aim for 2-3 minutes)

Record your screen. Have `results/baseline_results.json` and your
overlay images open and ready before you hit record — don't fumble
for files on camera.

## Beat-by-beat script

**[0:00-0:20] Problem, stated plainly**
"Optic disc and cup segmentation is used to screen for glaucoma. We
show that a standard U-Net trained on one hospital's images fails when
tested on a different hospital's images — and we fix it."

**[0:20-0:45] Show the failure**
Screen: your in-domain vs cross-domain result table.
"Trained on REFUGE, this model gets [X] Dice on REFUGE's own test
images — but only [Y] Dice on Drishti-GS, a completely different
imaging source it never saw during training. That's a [gap] point
drop, purely from domain shift."

**[0:45-1:15] Show it visually**
Screen: side-by-side segmentation overlays — baseline U-Net prediction
on a target-domain image (visibly wrong/noisy boundary) next to the
ground truth mask.
"Here's what that failure looks like — the model's cup boundary is
[describe the visible error]."

**[1:15-1:45] The fix**
Screen: architecture diagram or a code snippet of the alignment module.
"We add [mechanism name] at the U-Net bottleneck, which [one sentence
on what it does]. Same U-Net, same training budget — just this added."

**[1:45-2:15] Prove it worked**
Screen: overlay comparison — baseline prediction vs. aligned-model
prediction vs. ground truth, on the SAME target-domain image.
"With the alignment mechanism, Dice on that same target domain goes
from [Y] to [Z]."

**[2:15-2:45] The ablation — this is your credibility moment**
Screen: ablation table.
"To confirm this improvement is really from the mechanism and not just
extra capacity, we removed only the alignment module and kept
everything else identical. Cross-domain Dice dropped back to [number]
— confirming the mechanism itself is doing the work."

**[2:15-2:45] Live proof — run it on camera**
Open a terminal and run, live on screen:
`python src/live_demo.py`
Narrate while it runs: "Let me actually run this live — this is an
image from Drishti-GS the model has never seen during training."
Let the printed Dice numbers appear on screen as they print. When
the comparison image opens, point out the visual difference between
the baseline and IBN predictions vs. the ground truth.

**[2:45-3:00] Close**
"Full code, reproducible with one command, is in the repo linked
below. Thanks."

## Recording tips (given your time crunch)
- Do ONE take if you can — a slightly imperfect single take beats
  spending 30 minutes on retakes you don't have time for.
- Screen recording only is fine — you don't need to be on camera,
  narrate over your screen.
- Free tools: OBS Studio, or Windows Game Bar (Win+G) for a quick
  screen+audio recording with zero setup.
