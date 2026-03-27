"""File upload service using Supabase Storage."""

import uuid

from app.common.supabase import get_supabase_admin

BUCKET_NAME = "migration-uploads"
ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "text/plain",
    "text/xml",
    "application/json",
    "application/xml",
}


class UploadService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    def upload_file(
        self,
        user_id: str,
        session_id: str,
        file_bytes: bytes,
        file_name: str,
        mime_type: str,
    ) -> dict:
        """Upload a file to Supabase Storage and record metadata."""
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported file type: {mime_type}")

        # Generate storage path
        file_id = str(uuid.uuid4())
        ext = file_name.rsplit(".", 1)[-1] if "." in file_name else "bin"
        storage_path = f"{user_id}/{session_id}/{file_id}.{ext}"

        # Upload to Supabase Storage
        self.supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": mime_type},
        )

        # Save metadata
        result = (
            self.supabase.table("uploads")
            .insert({
                "session_id": session_id,
                "user_id": user_id,
                "storage_path": storage_path,
                "file_name": file_name,
                "mime_type": mime_type,
                "file_size": len(file_bytes),
            })
            .execute()
        )

        return result.data[0]

    def get_signed_url(self, upload_id: str, user_id: str) -> str:
        """Get a signed URL for downloading a file."""
        upload = (
            self.supabase.table("uploads")
            .select("storage_path")
            .eq("id", upload_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not upload.data:
            raise ValueError("Upload not found")

        url = self.supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path=upload.data["storage_path"],
            expires_in=3600,
        )
        return url["signedURL"]

    def get_file_bytes(self, upload_id: str, user_id: str) -> tuple[bytes, str]:
        """Download file bytes and return (bytes, mime_type)."""
        upload = (
            self.supabase.table("uploads")
            .select("storage_path, mime_type")
            .eq("id", upload_id)
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if not upload.data:
            raise ValueError("Upload not found")

        data = self.supabase.storage.from_(BUCKET_NAME).download(
            upload.data["storage_path"]
        )
        return data, upload.data["mime_type"]
