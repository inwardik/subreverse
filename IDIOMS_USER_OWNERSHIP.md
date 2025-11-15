# Idioms User Ownership Feature

## Overview

This feature adds user ownership and editorial capabilities to the Idioms module. Users can now:
- Create draft idioms (automatically when marking a subtitle pair as "idiom")
- Edit their own idioms (both draft and published)
- Add titles, explanations, and source information
- Publish idioms to make them visible to all users
- Delete their draft idioms
- View all published idioms plus their own drafts

## Changes Made

### Backend Changes

#### 1. Database Schema (`backend/src/infrastructure/database/postgres_models.py`)
- Added `user_id` field to `IdiomModel` (indexed for performance)
- Updated status values: 'active' → 'published'

#### 2. Domain Entities (`backend/src/domain/entities.py`)
- Added `user_id: str` field to `Idiom` entity

#### 3. Pydantic Schemas (`backend/src/infrastructure/database/postgres_schemas.py`)
- Updated `IdiomCreateSchema` to include `user_id`
- Updated status literals: 'active' → 'published'

#### 4. DTOs (`backend/src/application/dto.py`)
- Added `IdiomUpdateDTO` for PATCH operations
- Updated `IdiomResponseDTO` with `user_id` and `username` fields

#### 5. Repository Interface (`backend/src/domain/interfaces.py`)
- Added `get_for_user()` method to `IIdiomRepository`

#### 6. Repository Implementation (`backend/src/infrastructure/database/postgres.py`)
- Implemented `get_for_user()` - returns published idioms + user's drafts (user's drafts first)
- Updated `create()` to save `user_id`
- Updated `_model_to_entity()` to include `user_id`

#### 7. Service Layer (`backend/src/application/subtitle_service.py`)
- Updated idiom creation to include `user.id`
- Changed `_idiom_to_dto()` to async to fetch username
- Added `get_idioms_for_user()` method
- Added `update_idiom()` method with ownership check
- Added `delete_idiom()` method with ownership check (soft delete)

#### 8. API Routes (`backend/src/api/subtitle_routes.py`)
- Updated `GET /api/idioms` to use authentication (optional) and return personalized list
- Added `PATCH /api/idioms/{idiom_id}` endpoint (authenticated, owner-only)
- Added `DELETE /api/idioms/{idiom_id}` endpoint (authenticated, owner-only)

### Frontend Changes

#### 1. IdiomsView Component (`frontend/src/App.jsx`)
- Redesigned idiom cards with:
  - Clickable title (searches for quoted text)
  - Author username
  - Edit button (visible only for owned idioms)
  - Status badge (draft/published)
  - Better visual hierarchy
- Added authentication header to API requests
- Added edit functionality

#### 2. IdiomEditModal Component (`frontend/src/App.jsx`)
- New modal component for editing idioms
- Form fields: title, english, russian, explanation, source
- Three action buttons:
  - **Delete Draft** - soft-deletes the idiom (only for drafts)
  - **Save** - saves changes without changing status
  - **Publish** - saves and changes status to 'published'
- Error handling and loading states
- Ownership validation

### Database Migration

**File**: `backend/migrations/001_add_user_id_to_idioms.sql`

- Adds `user_id` column to idioms table
- Creates index on `user_id`
- Renames 'active' status to 'published'

**To apply**:
```bash
psql -h localhost -U subreverse -d subreverse -f backend/migrations/001_add_user_id_to_idioms.sql
```

## User Flow

### Creating an Idiom

1. User browses subtitle pairs
2. User clicks "idiom" button on a subtitle pair
3. System creates a **draft** idiom with:
   - `user_id` = current user's ID
   - `en` and `ru` from subtitle pair
   - `source` = filename
   - `status` = 'draft'

### Editing an Idiom

1. User navigates to Idioms page
2. User sees:
   - Their own draft idioms (first)
   - All published idioms
3. User clicks "Edit" button on their own idiom
4. Modal opens with form fields
5. User can:
   - **Save** - update fields without changing status
   - **Publish** - make idiom visible to everyone
   - **Delete Draft** - soft-delete the idiom (only for drafts)

### Viewing Idioms

- **Authenticated users**: See published idioms + their drafts
- **Anonymous users**: See only published idioms
- **Title click**: Redirects to search with quoted title text

## Security

- Ownership validation in backend
- User can only edit/delete their own idioms
- Returns HTTP 403 if user tries to modify someone else's idiom
- Authentication required for PATCH/DELETE operations

## API Endpoints

### GET /api/idioms
- **Auth**: Optional
- **Returns**: Published idioms + user's drafts (if authenticated)
- **Response**: `List[IdiomResponseDTO]`

### PATCH /api/idioms/{idiom_id}
- **Auth**: Required
- **Ownership**: Must own the idiom
- **Body**: `IdiomUpdateDTO`
- **Returns**: Updated `IdiomResponseDTO`

### DELETE /api/idioms/{idiom_id}
- **Auth**: Required
- **Ownership**: Must own the idiom
- **Action**: Soft-delete (sets status = 'deleted')
- **Returns**: 204 No Content

## Testing

### Manual Testing Steps

1. **Create idiom**:
   - Login
   - Search for a subtitle pair
   - Click "idiom" button
   - Verify draft created

2. **Edit idiom**:
   - Go to Idioms page
   - Find your draft idiom (should be first)
   - Click "Edit" button
   - Fill in title, explanation, source
   - Click "Save"
   - Verify changes saved

3. **Publish idiom**:
   - Edit your draft idiom
   - Fill in all fields
   - Click "Publish"
   - Verify status changed to 'published'
   - Logout and verify idiom visible to all

4. **Delete idiom**:
   - Create a new draft idiom
   - Click "Edit"
   - Click "Delete Draft"
   - Confirm deletion
   - Verify idiom no longer visible

5. **Title search**:
   - Create and publish an idiom with title
   - Click on the title
   - Verify redirects to search with quoted title

## Future Improvements

- [ ] Add pagination for idioms list
- [ ] Add filtering by author
- [ ] Add idiom ratings/likes
- [ ] Add comments on idioms
- [ ] Admin approval workflow for published idioms
- [ ] Bulk operations (publish multiple drafts)
- [ ] Export idioms as study cards
