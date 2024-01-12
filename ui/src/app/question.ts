export interface Question {
  id: number;
  question: string;
  unique_id: string;
  media: number;
  category: number;
  facility_type: number;
  survey123_field_type: number;
  lookup: number;
  default_unit: number;
  related_questions: Question[];
}
