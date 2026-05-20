# test_cleaning.py

from app.repositories.message_repository import (
    get_messages_by_workspace_id
)

from app.services.cleaning_service import (
    clean_text
)

from app.utils.text_utils import (
    extract_message_text
)


workspace_id = 126

data = get_messages_by_workspace_id(
    workspace_id=workspace_id
)

print("\n========== TEST CLEANING ==========\n")

for i, row in enumerate(data[:10], start=1):

    print(f"\n📌 MENSAJE #{i}")

    # mensaje raw
    message = row.get("message")

    # validación básica
    if not message:
        print("⚠️ Mensaje vacío")
        continue

    # texto original
    original_text = extract_message_text(message)

    # validación texto
    if not original_text:
        print("⚠️ No se pudo extraer texto")
        continue

    print("\n📝 ORIGINAL:")
    print(original_text)

    # cleaning
    cleaned_text = clean_text(original_text)

    print("\n🧹 CLEAN TEXT:")
    print(cleaned_text)

    print("\n" + "=" * 50)