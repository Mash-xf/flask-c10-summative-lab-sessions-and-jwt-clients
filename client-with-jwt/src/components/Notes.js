import React, { useEffect, useState } from "react";
import styled from "styled-components";
import { Button, Input, FormField, Label, Textarea } from "../styles";

function Notes({ user }) {
  const [notes, setNotes] = useState([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [errors, setErrors] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadNotes();
  }, []);

  function loadNotes() {
    setIsLoading(true);
    fetch("/notes", {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
      .then((r) => r.json())
      .then((data) => {
        setNotes(data.items || []);
      })
      .finally(() => setIsLoading(false));
  }

  function handleSubmit(e) {
    e.preventDefault();
    setErrors([]);
    const payload = { title, content };
    const method = editingId ? "PATCH" : "POST";
    const url = editingId ? `/notes/${editingId}` : "/notes";

    fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.error) {
          setErrors([data.error]);
          return;
        }
        setTitle("");
        setContent("");
        setEditingId(null);
        loadNotes();
      });
  }

  function handleEdit(note) {
    setEditingId(note.id);
    setTitle(note.title);
    setContent(note.content);
  }

  function handleDelete(id) {
    fetch(`/notes/${id}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
    })
      .then(() => loadNotes());
  }

  return (
    <Wrapper>
      <Header>
        <h2>My Notes</h2>
        <p>Welcome, {user?.username || "friend"}.</p>
      </Header>

      <Form onSubmit={handleSubmit}>
        <FormField>
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="A note title"
          />
        </FormField>
        <FormField>
          <Label htmlFor="content">Content</Label>
          <Textarea
            id="content"
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Write something down"
          />
        </FormField>
        <Buttons>
          <Button type="submit">
            {editingId ? "Save changes" : "Create note"}
          </Button>
          {editingId ? (
            <Button variant="outline" type="button" onClick={() => {
              setEditingId(null);
              setTitle("");
              setContent("");
            }}>
              Cancel
            </Button>
          ) : null}
        </Buttons>
        {errors.map((err) => (
          <Error key={err}>{err}</Error>
        ))}
      </Form>

      <List>
        {isLoading ? (
          <p>Loading notes…</p>
        ) : notes.length === 0 ? (
          <p>No notes yet. Create one above.</p>
        ) : (
          notes.map((note) => (
            <NoteCard key={note.id}>
              <div>
                <strong>{note.title}</strong>
                <p>{note.content}</p>
              </div>
              <Actions>
                <Button variant="outline" type="button" onClick={() => handleEdit(note)}>
                  Edit
                </Button>
                <Button type="button" onClick={() => handleDelete(note.id)}>
                  Delete
                </Button>
              </Actions>
            </NoteCard>
          ))
        )}
      </List>
    </Wrapper>
  );
}

const Wrapper = styled.section`
  max-width: 720px;
  margin: 24px auto;
  padding: 16px;
`;

const Header = styled.div`
  margin-bottom: 16px;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
`;

const Buttons = styled.div`
  display: flex;
  gap: 8px;
`;

const List = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const NoteCard = styled.article`
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
`;

const Actions = styled.div`
  display: flex;
  gap: 8px;
`;

const Error = styled.p`
  color: #b91c1c;
  margin: 0;
`;

export default Notes;
