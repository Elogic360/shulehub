export type SchoolType = 'PRIMARY' | 'SECONDARY' | 'COMBINED';
export type RoleType = 'SUPER_ADMIN' | 'SCHOOL_OWNER' | 'SCHOOL_ADMIN' | 'CLASS_TEACHER' | 'PARENT';
export type Language = 'sw' | 'en';

export interface User {
  id: string;
  email?: string;
  phone_number: string;
  full_name: string;
  roles: string[];
  is_superadmin?: boolean;
  school_id?: string;
  school_name?: string;
  school_type?: SchoolType;
  preferred_language?: Language;
}

export interface School {
  id: string;
  name: string;
  code: string;
  school_type: SchoolType;
  registration_number?: string;
  contact_email: string;
  contact_phone: string;
  region: string;
  district?: string;
  address?: string;
  is_verified: boolean;
  is_active: boolean;
}

export interface AcademicLevel {
  id: string;
  name: string;
  code: string;
  sequence_order: number;
  school_type: string;
}

export interface AcademicYear {
  id: string;
  name: string;
  start_date: string;
  end_date: string;
  is_current: boolean;
}

export interface ClassGroup {
  id: string;
  name: string;
  stream?: string;
  capacity: number;
  academic_level_id: string;
  academic_year_id: string;
  academic_level_name?: string;
  teacher?: {
    id: string;
    full_name: string;
    phone_number: string;
  } | null;
}

export interface Guardian {
  id: string;
  full_name: string;
  primary_phone: string;
  relationship: string;
  is_fee_payer: boolean;
  can_receive_results: boolean;
}

export interface Student {
  id: string;
  admission_number: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  gender: string;
  date_of_birth?: string;
  class_group_id?: string;
  class_name?: string;
  guardians: Guardian[];
}

export interface Campaign {
  id: string;
  title: string;
  message_content: string;
  targeting_mode: 'CLASS_BULK' | 'SELECTED_GUARDIANS' | 'INDIVIDUAL';
  status: string;
  recipient_count: number;
  delivered_count: number;
  failed_count: number;
  total_cost_tzs: number;
  created_at: string;
}

export interface Subject {
  id: string;
  name: string;
  code: string;
  school_type: string;
}

export interface Examination {
  id: string;
  name: string;
  exam_type: string;
  start_date: string;
  end_date: string;
  is_published: boolean;
}

export interface FeeInvoice {
  id: string;
  invoice_number: string;
  student_id: string;
  student_name: string;
  admission_number: string;
  total_amount_tzs: number;
  balance_due_tzs: number;
  status: string;
  due_date: string;
  items_count: number;
}

export interface Meeting {
  id: string;
  title: string;
  description?: string;
  meeting_date: string;
  start_time: string;
  end_time: string;
  venue: string;
  invitations_count: number;
  confirmed_count: number;
  declined_count: number;
}
