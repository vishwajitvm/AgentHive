import os
import ast
import math
import hashlib
import hmac
import base64
import zipfile
import tarfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from app.tools.base import BaseTool
from app.logging.logger import get_logger

logger = get_logger(__name__)

WORKSPACE_DIR = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
os.makedirs(WORKSPACE_DIR, exist_ok=True)

class CalculatorTool(BaseTool):
    @property
    def slug(self) -> str: return "calculator_tool"
    @property
    def name(self) -> str: return "Scientific Calculator & Math Evaluator"
    @property
    def description(self) -> str:
        return "Safely evaluates math expressions, formulas, and scientific calculations. Arguments: expression (math string, e.g. 'sqrt(16) + sin(pi/2) * 5')."

    async def run(self, **kwargs) -> str:
        expression = kwargs.get("expression") or kwargs.get("formula") or kwargs.get("math") or kwargs.get("equation") or ""
        expression = str(expression).strip()
        if not expression:
            return "Error: expression parameter is required."

        try:
            try:
                import sympy
                res = sympy.sympify(expression)
                val = float(res.evalf())
                return f"Math Result: {expression} = {res} ({val})"
            except Exception:
                pass

            # Safe AST math evaluation fallback
            allowed_names = {
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "exp": math.exp, "pow": math.pow, "abs": abs,
                "floor": math.floor, "ceil": math.ceil, "pi": math.pi, "e": math.e
            }

            def eval_node(node):
                if isinstance(node, ast.Constant):
                    return node.value
                elif isinstance(node, ast.BinOp):
                    left = eval_node(node.left)
                    right = eval_node(node.right)
                    if isinstance(node.op, ast.Add): return left + right
                    elif isinstance(node.op, ast.Sub): return left - right
                    elif isinstance(node.op, ast.Mult): return left * right
                    elif isinstance(node.op, ast.Div): return left / right
                    elif isinstance(node.op, ast.Pow): return left ** right
                    elif isinstance(node.op, ast.Mod): return left % right
                elif isinstance(node.op, ast.UnaryOp):
                    operand = eval_node(node.operand)
                    if isinstance(node.op, ast.UAdd): return +operand
                    elif isinstance(node.op, ast.USub): return -operand
                elif isinstance(node, ast.Call):
                    func_name = node.func.id
                    if func_name in allowed_names:
                        args = [eval_node(arg) for arg in node.args]
                        return allowed_names[func_name](*args)
                elif isinstance(node, ast.Name):
                    if node.id in allowed_names:
                        return allowed_names[node.id]
                raise ValueError(f"Unsupported mathematical syntax: {ast.dump(node)}")

            parsed = ast.parse(expression, mode='eval')
            result = eval_node(parsed.body)
            return f"Math Result: {expression} = {result}"

        except Exception as e:
            return f"CalculatorTool error: {str(e)}"

class DatetimeTool(BaseTool):
    @property
    def slug(self) -> str: return "datetime_tool"
    @property
    def name(self) -> str: return "Date, Timezone & Cron Calculator"
    @property
    def description(self) -> str:
        return "Performs timezone conversions, date arithmetic, ISO formatting, and timestamp calculations. Arguments: action ('current'/'convert_tz'/'diff'/'add_time'), date_str (optional), timezone (optional, default 'UTC'), days/hours/minutes (optional numbers for arithmetic)."

    async def run(self, **kwargs) -> str:
        action = str(kwargs.get("action", "current")).strip().lower()
        date_str = kwargs.get("date_str") or kwargs.get("date") or kwargs.get("time") or ""
        date_str = str(date_str).strip()
        tz_name = str(kwargs.get("timezone", "UTC")).strip()
        days = float(kwargs.get("days", 0))
        hours = float(kwargs.get("hours", 0))
        minutes = float(kwargs.get("minutes", 0))

        try:
            now_utc = datetime.now(timezone.utc)

            if action == "current":
                return (
                    f"Current Date & Time:\n"
                    f"- UTC ISO: {now_utc.isoformat()}\n"
                    f"- Date: {now_utc.strftime('%Y-%m-%d')}\n"
                    f"- Time: {now_utc.strftime('%H:%M:%S %Z')}\n"
                    f"- Unix Timestamp: {int(now_utc.timestamp())}"
                )

            elif action == "add_time":
                base_dt = datetime.fromisoformat(date_str) if date_str else now_utc
                delta = timedelta(days=days, hours=hours, minutes=minutes)
                result_dt = base_dt + delta
                return (
                    f"Date Arithmetic Result:\n"
                    f"- Original: {base_dt.isoformat()}\n"
                    f"- Offset: +{days} days, +{hours} hours, +{minutes} minutes\n"
                    f"- Result ISO: {result_dt.isoformat()}"
                )

            elif action == "diff":
                date_str2 = kwargs.get("date_str2", "").strip()
                if not date_str or not date_str2:
                    return "Error: Both date_str and date_str2 parameters are required for diff action."
                dt1 = datetime.fromisoformat(date_str)
                dt2 = datetime.fromisoformat(date_str2)
                diff = dt2 - dt1
                return (
                    f"Date Difference Result:\n"
                    f"- Date 1: {dt1.isoformat()}\n"
                    f"- Date 2: {dt2.isoformat()}\n"
                    f"- Difference: {diff.days} days, {diff.seconds // 3600} hours, {(diff.seconds % 3600) // 60} minutes ({diff.total_seconds()} total seconds)"
                )

            else:
                return f"Error: Invalid action '{action}'. Supported: current, add_time, diff."
        except Exception as e:
            return f"DatetimeTool error: {str(e)}"

class ImageMetadataTool(BaseTool):
    @property
    def slug(self) -> str: return "image_metadata_tool"
    @property
    def name(self) -> str: return "Image EXIF & Metadata Reader"
    @property
    def description(self) -> str:
        return "Reads image dimensions, color format, DPI, and EXIF tags from workspace image files. Arguments: filename."

    async def run(self, **kwargs) -> str:
        filename = kwargs.get("filename") or kwargs.get("file") or kwargs.get("name") or kwargs.get("image") or ""
        filename = str(filename).strip()
        if not filename:
            return "Error: filename parameter is required."

        filepath = os.path.join(WORKSPACE_DIR, os.path.basename(filename))
        if not os.path.exists(filepath):
            return f"Error: File '{filename}' not found in workspace."

        try:
            from PIL import Image, ExifTags
            with Image.open(filepath) as img:
                info = [
                    f"Image Metadata for '{filename}':",
                    f"- Format: {img.format}",
                    f"- Dimensions: {img.width} x {img.height} pixels",
                    f"- Color Mode: {img.mode}",
                    f"- DPI: {img.info.get('dpi', 'N/A')}"
                ]

                # EXIF metadata extraction
                exif_data = img._getexif()
                if exif_data:
                    info.append("\nEXIF Camera Tags:")
                    count = 0
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        val_str = str(value)[:50]
                        info.append(f"  {tag}: {val_str}")
                        count += 1
                        if count >= 15:
                            info.append("  [TRUNCATED]")
                            break
                else:
                    info.append("\nNo EXIF camera tags found in image.")

                return "\n".join(info)
        except Exception as e:
            return f"ImageMetadataTool error: {str(e)}"

class HashCryptoTool(BaseTool):
    @property
    def slug(self) -> str: return "hash_crypto_tool"
    @property
    def name(self) -> str: return "Crypto Hash & Checksum Tool"
    @property
    def description(self) -> str:
        return "Generates cryptographic hashes (MD5, SHA256, SHA512), Base64 encoding/decoding, or HMAC signatures. Arguments: action ('hash'/'base64_encode'/'base64_decode'/'hmac'), data, algorithm (for hash: md5/sha256/sha512, default 'sha256'), secret_key (for hmac)."

    async def run(self, **kwargs) -> str:
        action = str(kwargs.get("action", "hash")).strip().lower()
        data = kwargs.get("data") or kwargs.get("text") or kwargs.get("content") or ""
        algorithm = kwargs.get("algorithm", "sha256").strip().lower()
        secret_key = kwargs.get("secret_key", "")

        if data is None:
            return "Error: data parameter is required."

        try:
            raw_bytes = data.encode("utf-8")

            if action == "hash":
                if algorithm == "md5":
                    res = hashlib.md5(raw_bytes).hexdigest()
                elif algorithm == "sha512":
                    res = hashlib.sha512(raw_bytes).hexdigest()
                else:
                    res = hashlib.sha256(raw_bytes).hexdigest()
                return f"{algorithm.upper()} Hash Result:\n{res}"

            elif action == "base64_encode":
                encoded = base64.b64encode(raw_bytes).decode("utf-8")
                return f"Base64 Encoded Output:\n{encoded}"

            elif action == "base64_decode":
                decoded = base64.b64decode(data).decode("utf-8")
                return f"Base64 Decoded Output:\n{decoded}"

            elif action == "hmac":
                if not secret_key:
                    return "Error: secret_key is required for hmac action."
                digestmod = hashlib.sha256
                if algorithm == "md5": digestmod = hashlib.md5
                elif algorithm == "sha512": digestmod = hashlib.sha512
                signature = hmac.new(secret_key.encode("utf-8"), raw_bytes, digestmod).hexdigest()
                return f"HMAC-{algorithm.upper()} Signature:\n{signature}"

            else:
                return f"Error: Invalid action '{action}'. Supported: hash, base64_encode, base64_decode, hmac."
        except Exception as e:
            return f"HashCryptoTool error: {str(e)}"

class ZipArchiverTool(BaseTool):
    @property
    def slug(self) -> str: return "zip_archiver_tool"
    @property
    def name(self) -> str: return "ZIP & Archive Manager"
    @property
    def description(self) -> str:
        return "Creates, extracts, or inspects ZIP archives in workspace. Arguments: action ('compress'/'extract'/'list'), zip_filename, filenames (list of files for compress), extract_to (optional subfolder for extract)."

    async def run(self, **kwargs) -> str:
        action = str(kwargs.get("action", "")).strip().lower()
        zip_filename = kwargs.get("zip_filename") or kwargs.get("zip") or kwargs.get("archive") or kwargs.get("filename") or kwargs.get("file") or ""
        zip_filename = str(zip_filename).strip()
        filenames = kwargs.get("filenames") or kwargs.get("files") or kwargs.get("names") or []
        extract_to = str(kwargs.get("extract_to", "")).strip()

        if action not in ["compress", "extract", "list"]:
            return "Error: action must be 'compress', 'extract', or 'list'."
        if not zip_filename:
            return "Error: zip_filename parameter is required."
        if not zip_filename.endswith(".zip"):
            zip_filename += ".zip"

        zip_path = os.path.join(WORKSPACE_DIR, os.path.basename(zip_filename))

        try:
            if action == "compress":
                if not filenames:
                    return "Error: filenames parameter (list of workspace filenames) is required for compression."
                if isinstance(filenames, str):
                    filenames = [f.strip() for f in filenames.split(",") if f.strip()]

                added_files = []
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for fn in filenames:
                        fp = os.path.join(WORKSPACE_DIR, os.path.basename(fn))
                        if os.path.exists(fp):
                            zf.write(fp, os.path.basename(fn))
                            added_files.append(os.path.basename(fn))

                return f"Successfully created ZIP archive '{zip_filename}' containing {len(added_files)} files: {', '.join(added_files)}"

            elif action == "list":
                if not os.path.exists(zip_path):
                    return f"Error: Archive '{zip_filename}' not found in workspace."
                with zipfile.ZipFile(zip_path, "r") as zf:
                    infos = zf.infolist()
                    items = [f"- {info.filename} ({info.file_size} bytes)" for info in infos]
                    return f"Contents of '{zip_filename}' ({len(infos)} files):\n" + "\n".join(items)

            elif action == "extract":
                if not os.path.exists(zip_path):
                    return f"Error: Archive '{zip_filename}' not found in workspace."
                dest_dir = os.path.join(WORKSPACE_DIR, os.path.basename(extract_to)) if extract_to else WORKSPACE_DIR
                os.makedirs(dest_dir, exist_ok=True)

                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(dest_dir)
                    names = zf.namelist()
                    return f"Extracted {len(names)} files from '{zip_filename}' to workspace directory '{os.path.basename(dest_dir)}'."

        except Exception as e:
            return f"ZipArchiverTool error: {str(e)}"
