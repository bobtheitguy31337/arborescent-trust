# Testing Guide - Arborescent Trust

Complete guide for testing the Twitter clone with trust system.

## Prerequisites

- Backend running on port 8000
- Admin dashboard (frontend) on port 5173
- User web app on port 5174

---

## Quick Start Testing

### 1. Start All Services

```bash
# Terminal 1: Backend (if not running)
cd backend
docker-compose up -d

# Terminal 2: Admin Dashboard
cd frontend
npm run dev

# Terminal 3: User Web App
cd web
npm run dev
```

### 2. Verify Everything is Running

```bash
# Check backend
curl http://localhost:8000/health

# Open in browser:
# - User App: http://localhost:5174
# - Admin Dashboard: http://localhost:5173
# - API Docs: http://localhost:8000/docs
```

---

## Test Scenarios

### Scenario 1: Admin Login & First Post

**Goal**: Login as admin and create your first post

1. **Navigate to User App**
   - Open: http://localhost:5174

2. **Login**
   - Email: `admin@example.com`
   - Password: `changeme` (or your custom password from .env)
   - Click "Sign In"

3. **Verify Login Success**
   - You should see the home feed
   - Sidebar should show your username
   - Trust badge should show "🛡️ Core"

4. **Create First Post**
   - Type in the composer: "Hello Arborescent! 🌳"
   - Click "Post"
   - Post should appear immediately in feed

5. **Verify Post Display**
   - Your post should show your username
   - Trust badge should be visible
   - Timestamp should show "just now"

**Expected Result**: ✅ Post created and displayed with trust badge

---

### Scenario 2: Upload Media

**Goal**: Create post with image

1. **Create Post with Image**
   - Click the image icon (📷) in composer
   - Select an image file (JPG, PNG, GIF)
   - Wait for upload (spinner appears)
   - Image preview should appear
   - Add text: "Check out this image!"
   - Click "Post"

2. **Verify Media Display**
   - Post should show image inline
   - Image should be clickable/viewable
   - Delete button (X) should appear on hover

3. **Test Multiple Media**
   - Upload 2-4 images in one post
   - They should display in a grid layout
   - Try mixing images and videos

**Expected Result**: ✅ Media uploads and displays correctly

---

### Scenario 3: User Registration & Invite System

**Goal**: Register a new user with invite code

1. **Get Invite Code (Admin Dashboard)**
   - Open: http://localhost:5173
   - Login with admin credentials
   - Go to "Invites" section
   - Click "Create Invite Token"
   - Copy the generated token

2. **Register New User**
   - Open: http://localhost:5174/register (incognito/private window)
   - Paste invite code
   - Fill in:
     - Email: `alice@example.com`
     - Username: `alice`
     - Password: `password123`
   - Click "Create Account"

3. **Verify Registration**
   - Should redirect to home feed
   - New user should be logged in
   - Trust badge should show "🌱 Seedling" (new account)

4. **Check Invite Tree (Admin Dashboard)**
   - Go back to admin dashboard
   - Navigate to "Tree View"
   - Search for admin email: `admin@example.com`
   - Should see Alice as a child node

**Expected Result**: ✅ New user registered and appears in invite tree

---

### Scenario 4: Social Interactions

**Goal**: Test likes, reposts, and replies

1. **Create a Post as Alice**
   - Login as Alice
   - Post: "My first post!"

2. **Like the Post (as Admin)**
   - Login as admin (different browser/incognito)
   - Find Alice's post in feed (follow Alice first if needed)
   - Click heart icon ❤️
   - Heart should turn red
   - Count should increase

3. **Verify Notification (as Alice)**
   - Switch back to Alice's session
   - Click "Notifications" in sidebar
   - Should see: "admin liked your post"
   - Notification should have blue dot (unread)
   - Click notification to mark as read

4. **Repost**
   - As admin, click repost icon 🔁 on Alice's post
   - Icon should turn green
   - Count should increase

5. **Reply**
   - Click reply icon 💬 on Alice's post
   - Reply composer should appear
   - Type: "Welcome to Arborescent!"
   - Click "Reply"
   - Reply should appear under original post

**Expected Result**: ✅ All interactions work and notifications are sent

---

### Scenario 5: Follow System

**Goal**: Test following users and feed

1. **Follow a User**
   - As admin, navigate to Alice's profile (click username)
   - Click "Follow" button
   - Button should change to "Following"
   - Follower count should increase

2. **Verify Feed**
   - Go to home feed
   - Alice's posts should now appear in your feed
   - Both your posts and Alice's posts should be visible

3. **Unfollow**
   - Click "Following" button
   - Should change back to "Follow"
   - Alice's new posts won't appear in feed (old ones remain)

**Expected Result**: ✅ Following affects feed content

---

### Scenario 6: Trust Badges

**Goal**: Verify trust system integration

1. **Check Badge Display**
   - All posts should show trust badges
   - Admin should have "🛡️ Core"
   - New users should have "🌱 Seedling"
   - Badges should be color-coded

2. **Test Status Changes (Admin Dashboard)**
   - Go to admin dashboard
   - Navigate to "Users"
   - Find Alice
   - Click "Flag User"
   - Provide reason: "Testing"

3. **Verify Badge Change**
   - Go back to user app
   - Alice's posts should now show "🌿 Branch" badge
   - Badge should be yellow/warning color

**Expected Result**: ✅ Trust badges reflect user status

---

### Scenario 7: Infinite Scroll

**Goal**: Test feed pagination

1. **Create Multiple Posts**
   - Create 25+ posts (or use multiple users)
   - Mix of text, images, and videos

2. **Test Scroll**
   - Scroll down in the feed
   - When you reach the bottom, more posts should load automatically
   - Loading spinner should appear briefly
   - New posts should append to bottom

3. **Verify "End of Feed"**
   - Keep scrolling until no more posts
   - Should see: "You've reached the end"

**Expected Result**: ✅ Infinite scroll loads more content

---

### Scenario 8: Media Types

**Goal**: Test all media types

1. **Test Image Upload**
   - JPG: ✅ Should work
   - PNG: ✅ Should work
   - GIF: ✅ Should work and animate
   - WEBP: ✅ Should work

2. **Test Video Upload**
   - MP4: ✅ Should work with player controls
   - MOV: ✅ Should work
   - WEBM: ✅ Should work

3. **Test Size Limits**
   - Images: Max 10MB
   - Videos: Max 100MB
   - Should show error if exceeded

4. **Test Multiple Media**
   - 1 image: Displays full width
   - 2 images: 2-column grid
   - 3-4 images: 2x2 grid

**Expected Result**: ✅ All media types display correctly

---

## API Testing

### Test with cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"changeme"}' | jq .

# Get feed (save token first)
TOKEN="your_access_token_here"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/posts/feed | jq .

# Create post
curl -X POST http://localhost:8000/api/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Testing from curl!"}' | jq .

# Like a post
POST_ID="post_id_here"
curl -X POST "http://localhost:8000/api/social/posts/$POST_ID/like" \
  -H "Authorization: Bearer $TOKEN"
```

### Test with Postman/Insomnia

1. Import the OpenAPI spec from: http://localhost:8000/openapi.json
2. Set authorization header: `Bearer <token>`
3. Test all endpoints

---

## Performance Testing

### Load Testing with Multiple Users

1. **Create Multiple Test Users**
   ```bash
   # Generate 10 invite codes
   # Register 10 users (alice, bob, charlie, etc.)
   ```

2. **Create Test Posts**
   - Each user creates 10 posts
   - Include images in some posts
   - Create reply threads

3. **Test Feed Performance**
   - Scroll through feed with 100+ posts
   - Should load smoothly
   - No lag or stuttering

4. **Test Notifications**
   - Generate 50+ notifications
   - Check loading time
   - Test mark all as read

---

## Error Handling Testing

### Test Error Cases

1. **Invalid Login**
   - Wrong email: Should show error
   - Wrong password: Should show error
   - Empty fields: Should prevent submission

2. **Invalid Registration**
   - Invalid invite code: Should show error
   - Duplicate email: Should show error
   - Duplicate username: Should show error
   - Short password: Should show error

3. **Post Validation**
   - Empty post: Should prevent submission
   - >280 chars: Should show error/prevent posting
   - Invalid file type: Should show error

4. **Network Errors**
   - Stop backend
   - Try to create post
   - Should show error message
   - Should not crash frontend

---

## Mobile Testing

### Responsive Design

1. **Chrome DevTools**
   - Open DevTools (F12)
   - Click device toolbar (Ctrl+Shift+M)
   - Test on:
     - iPhone SE (375px)
     - iPhone 12 Pro (390px)
     - iPad (768px)

2. **Verify Layout**
   - Sidebar should hide on mobile
   - Posts should be full width
   - Buttons should be touch-friendly
   - Text should be readable

---

## Browser Compatibility

### Test on Multiple Browsers

- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)

### Features to Test Per Browser
- Media upload
- Video playback
- Infinite scroll
- Notifications
- Image previews

---

## Database Testing

### Verify Data Persistence

1. **Create Posts**
   - Create several posts
   - Refresh browser
   - Posts should still be there

2. **Restart Backend**
   ```bash
   docker-compose restart api
   ```
   - Wait 10 seconds
   - Refresh user app
   - All data should persist

3. **Check Database**
   ```bash
   docker-compose exec postgres psql -U postgres -d invite_tree
   
   # Count posts
   SELECT COUNT(*) FROM posts;
   
   # Count users
   SELECT COUNT(*) FROM users;
   
   # View recent posts
   SELECT content, created_at FROM posts ORDER BY created_at DESC LIMIT 5;
   ```

---

## Common Issues & Solutions

### Issue: Blank Page After Login
**Solution**: Check browser console for errors. Likely missing API fields.

### Issue: Media Upload Fails
**Solution**: Check media directory permissions. Ensure `/app/media` exists in container.

### Issue: Infinite Scroll Doesn't Load More
**Solution**: Check network tab. Verify pagination is working. Check `has_more` field.

### Issue: Notifications Don't Appear
**Solution**: Refresh page. Check notification endpoint. Verify user_id matches.

### Issue: Trust Badges Don't Show
**Solution**: Check user status. Verify badge component is rendering.

---

## Testing Checklist

Use this checklist to verify all features:

### Authentication
- [ ] Login with valid credentials
- [ ] Login with invalid credentials (error shown)
- [ ] Register with invite code
- [ ] Register with invalid code (error shown)
- [ ] Logout
- [ ] Token refresh on 401

### Posts
- [ ] Create text post
- [ ] Create post with 1 image
- [ ] Create post with 4 images
- [ ] Create post with video
- [ ] Delete own post
- [ ] Cannot delete others' posts
- [ ] 280 character limit enforced
- [ ] Empty post prevented

### Social
- [ ] Like post
- [ ] Unlike post
- [ ] Repost
- [ ] Reply to post
- [ ] Follow user
- [ ] Unfollow user
- [ ] View followers list
- [ ] View following list

### Feed
- [ ] Personalized feed loads
- [ ] Infinite scroll works
- [ ] New posts appear at top
- [ ] Feed updates after posting
- [ ] Empty state shows when no posts

### Notifications
- [ ] Like notification received
- [ ] Repost notification received
- [ ] Reply notification received
- [ ] Follow notification received
- [ ] Unread count shows
- [ ] Mark as read works
- [ ] Mark all as read works

### Trust System
- [ ] Trust badges show on posts
- [ ] Trust badges show on profiles
- [ ] Core member badge (🛡️)
- [ ] Status badges (🌱🌿🌳)
- [ ] Badge colors correct

### UI/UX
- [ ] Dark theme consistent
- [ ] Icons display correctly
- [ ] Loading states show
- [ ] Error messages clear
- [ ] Responsive on mobile
- [ ] Smooth animations

---

## Automated Testing (Future)

### Setup Jest Tests
```bash
cd web
npm install -D @testing-library/react @testing-library/jest-dom vitest
```

### Example Test
```typescript
import { render, screen } from '@testing-library/react';
import { PostCard } from './components/PostCard';

test('renders post content', () => {
  const post = { content: 'Test post', ... };
  render(<PostCard post={post} />);
  expect(screen.getByText('Test post')).toBeInTheDocument();
});
```

---

## Ready to Test!

Start with Scenario 1 (Admin Login & First Post) and work your way through.

**Pro tip**: Use Chrome DevTools Network tab to debug API calls!

