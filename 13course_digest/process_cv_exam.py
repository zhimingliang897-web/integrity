import os
import sys
from pathlib import Path
import extract
import analyze
import config
import prompts

def main():
    cv_dir = Path(__file__).parent / "cache" / "ACV"
    pdf_files = sorted(list(cv_dir.glob("*.pdf")))
    
    if not pdf_files:
        print(f"No PDF files found in {cv_dir}")
        return

    all_texts = []
    for pdf in pdf_files:
        print(f"Extracting: {pdf.name}...")
        text = extract.extract_pdf(str(pdf))
        all_texts.append(f"--- FILE: {pdf.name} ---\n{text}")

    combined_text = "\n\n".join(all_texts)
    
    # Check total length to avoid token limits, but for 7 PDFs it should usually fit in modern models
    # if using qwen-max or llama-3.3-70b.
    
    print("\nGenerating Exam Prep Material with AI (Multi-stage to avoid truncation)...")
    
    system_prompt = "You are an expert academic tutor in Computer Vision. Output in Chinese (except technical terms)."
    
    try:
        # Stage 1: Analysis
        print("[Stage 1/3] Generating Exam Points Analysis...")
        analysis_prompt = prompts.build_cv_analysis_prompt(combined_text)
        analysis_result = analyze._call_llm(system_prompt, analysis_prompt)
        
        # Stage 2: Questions 1-20
        print("[Stage 2/3] Generating MCQ 1-20...")
        q1_prompt = prompts.build_cv_questions_part1_prompt(combined_text)
        q1_result = analyze._call_llm(system_prompt, q1_prompt)
        
        # Stage 3: Questions 21-40 + Fill-in
        print("[Stage 3/3] Generating MCQ 21-40 and Fill-in questions...")
        q2_prompt = prompts.build_cv_questions_part2_prompt(combined_text)
        q2_result = analyze._call_llm(system_prompt, q2_prompt)
        
        # Combine all parts
        final_result = f"""# 📘 AI6126 Advanced Computer Vision — 考前冲刺精要
*Based on 7 Lectures | Multi-stage Balanced Generation*

---
{analysis_result}

---
## 第二部分：模拟备考练习题（含详尽题解）

### MCQ 1-20
{q1_result}

---
### MCQ 21-40 + 填空题
{q2_result}
"""
        
        output_dir = Path(config.OUTPUT_DIR)
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "CV_Final_Exam_Prep.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_result)
            
        print(f"\nSuccessfully generated full exam prep material: {output_file}")
        
    except Exception as e:
        print(f"Error during AI generation: {e}")

if __name__ == "__main__":
    main()
