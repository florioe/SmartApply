import pypandoc
import os
import shutil

def convert_md_to_docx(md_file_path, docx_output_path, reference_docx_path):
    """
    Converts a Markdown file to a DOCX file using Pandoc.
    Requires Pandoc to be installed and accessible in the system's PATH.
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(docx_output_path), exist_ok=True)
        
        # Use pypandoc to convert Markdown to DOCX
        # The --reference-doc argument applies styles from an existing DOCX
        pypandoc.convert_file(
            md_file_path, 
            'docx', 
            outputfile=docx_output_path, 
            extra_args=['--reference-doc={}'.format(reference_docx_path)]
        )
        print("Successfully converted {} to {}".format(md_file_path, docx_output_path))
        return True
    except FileNotFoundError:
        print("Error: Pandoc is not installed or not found in PATH. Please install Pandoc.")
        print("You can download it from: https://pandoc.org/installing.html")
        return False
    except RuntimeError as e:
        print("Error during Pandoc conversion: {}".format(e))
        print("Ensure the reference DOCX path is correct and the Markdown content is valid.")
        return False
    except Exception as e:
        print("An unexpected error occurred during DOCX conversion: {}".format(e))
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert a Markdown file to a DOCX file.")
    parser.add_argument('md_file_path', type=str, help='Path to the input Markdown file.')
    parser.add_argument('docx_output_path', type=str, help='Path to the output DOCX file.')
    parser.add_argument('reference_docx_path', type=str, help='Path to the reference DOCX file for styling.')
    
    args = parser.parse_args()

    convert_md_to_docx(args.md_file_path, args.docx_output_path, args.reference_docx_path)
